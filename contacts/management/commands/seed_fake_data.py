import random
import uuid
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker
from django.utils.text import slugify


# TODO: adjust to your real app paths
from audience.models import Audience
from contacts.models import Contact # <-- change 'your_app' if needed

fake = Faker()

# Simple E.164 generator without external deps
# You can tune the per-country lengths to your needs.
COUNTRY_DIAL_CODES = {
    "EG": "+20",   # Egypt
    "SA": "+966",  # Saudi Arabia
    "AE": "+971",  # UAE
    "US": "+1",    # USA
    "GB": "+44",   # UK
    "DE": "+49",   # Germany
    "FR": "+33",   # France
}

COUNTRY_NUMBER_LENGTHS = {   # digits AFTER the country code (national significant number)
    "EG": (9, 10),
    "SA": (8, 9),
    "AE": (8, 9),
    "US": (10, 10),
    "GB": (9, 10),
    "DE": (9, 11),
    "FR": (9, 9),
}

def random_e164(country_code=None):
    """Return an E.164 phone like +201234567890."""
    if country_code not in COUNTRY_DIAL_CODES:
        country_code = random.choice(list(COUNTRY_DIAL_CODES.keys()))
    dial = COUNTRY_DIAL_CODES[country_code]
    lo, hi = COUNTRY_NUMBER_LENGTHS.get(country_code, (9, 10))
    length = random.randint(lo, hi)
    # first digit cannot be 0 to avoid leading zeros after country code
    first = str(random.randint(1, 9))
    rest = "".join(str(random.randint(0, 9)) for _ in range(length - 1))
    return f"{dial}{first}{rest}"


class Command(BaseCommand):
    help = "Seed DB with fake audiences and contacts (phones in E.164, optional tags)."

    def add_arguments(self, parser):
        parser.add_argument("--audiences", type=int, default=10, help="How many audiences (default: 10)")
        parser.add_argument("--min-contacts", type=int, default=100, help="Min contacts per audience (default: 100)")
        parser.add_argument("--max-contacts", type=int, default=450, help="Max contacts per audience (default: 450)")
        parser.add_argument("--user-id", type=int, default=None, help="user user id (optional)")
        parser.add_argument("--batch-size", type=int, default=1000, help="bulk_create batch size (default: 1000)")

        # Tagging options
        parser.add_argument(
            "--tag-pool",
            type=str,
            default="vip,lead,prospect,customer,newsletter,trial,bounced,hot,cold,partner",
            help="Comma-separated list of tag names to sample from.",
        )
        parser.add_argument(
            "--tag-prob",
            type=float,
            default=0.6,
            help="Probability that a contact gets tags at all (0.0–1.0). Default: 0.6",
        )
        parser.add_argument(
            "--max-tags-per-contact",
            type=int,
            default=3,
            help="Max tags to assign for a single contact (1..N). Default: 3",
        )

        parser.add_argument(
            "--phone-country",
            type=str,
            default=None,
            help="Force a specific country code for all phones (e.g., EG, SA, AE, US...). If omitted, random per contact.",
        )

    def handle(self, *args, **options):
        n_audiences = options["audiences"]
        min_contacts = options["min_contacts"]
        max_contacts = options["max_contacts"]
        user_id = options["user_id"]
        batch_size = options["batch_size"]

        # tags
        raw_tags = [t.strip().lower() for t in options["tag_pool"].split(",") if t.strip()]
        tag_prob = float(options["tag_prob"])
        max_tags_per_contact = int(options["max_tags_per_contact"])
        phone_country = options["phone_country"]

        if max_tags_per_contact < 1:
            max_tags_per_contact = 1
        if not 0.0 <= tag_prob <= 1.0:
            tag_prob = 0.6

        User = get_user_model()
        user = None
        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User id {user_id} does not exist."))
                return


            created_audiences = []
            for i in range(n_audiences):
                aud_name = f"{fake.company()} Audience {i+1}"
                aud_description = fake.sentence(nb_words=8)

                aud_kwargs = dict(name=aud_name, description=aud_description)
                if user is not None:
                    # auto-detect common user field names
                    audience_fields = {f.name for f in Audience._meta.get_fields()}
                    for candidate in ("user", "user", "created_by", "creator", "account"):
                        if candidate in audience_fields:
                            aud_kwargs[candidate] = user
                            break

                # If your model sets slug in save()/signals, this ensures it runs
                # Also keeps UUID default generation on the model working as intended
                aud = Audience.objects.create(**aud_kwargs)
                created_audiences.append(aud)

            self.stdout.write(self.style.SUCCESS(f"Created {len(created_audiences)} audiences."))
            audiences = created_audiences

            # status choices fallback
            statuses = [
                c[0] for c in getattr(
                    Contact, "STATUS_CHOICES",
                    (("active", "active"), ("bounced", "bounced"), ("archived", "archived"))
                )
            ]

            total_contacts = 0

            for aud in audiences:
                count = random.randint(min_contacts, max_contacts)
                total_contacts += count
                self.stdout.write(f"Seeding {count} contacts for audience '{aud.name}' (id={aud.pk})...")

                contacts_batch = []
                # ensure uniqueness per audience
                seen_emails = set()

                for _ in range(count):
                    email = fake.unique.email().lower()
                    if email in seen_emails:
                        email = f"{uuid.uuid4().hex[:8]}_{email}"
                    seen_emails.add(email)

                    first = fake.first_name()
                    last = fake.last_name()
                    phone = random_e164(phone_country)
                    status = random.choice(statuses)

                    contact_kwargs = dict(
                        audience=aud,
                        email=email,
                        first_name=first,
                        last_name=last,
                        phone=phone,
                        status=status,
                        source="seed-script",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )

                    # UUID PK support
                    if getattr(Contact._meta.pk, "get_internal_type")() == "UUIDField":
                        contact_kwargs["id"] = uuid.uuid4()

                    # Optional TAGS (ArrayField of strings)
                    if raw_tags and random.random() < tag_prob:
                        # sample 1..max_tags_per_contact (cap by pool size)
                        k = random.randint(1, min(max_tags_per_contact, len(raw_tags)))
                        # ensure stable, lowercased tags
                        tags = random.sample(raw_tags, k)
                        contact_kwargs["tags"] = tags  # works fine with ArrayField in bulk_create

                    contacts_batch.append(Contact(**contact_kwargs))

                    if len(contacts_batch) >= batch_size:
                        Contact.objects.bulk_create(contacts_batch)
                        contacts_batch = []

                if contacts_batch:
                    Contact.objects.bulk_create(contacts_batch)

                self.stdout.write(self.style.SUCCESS(f"  -> Done: {count} contacts for audience {aud.pk}"))

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete. Audiences: {n_audiences}, Contacts: ~{total_contacts}"
        ))
