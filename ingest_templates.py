import os
import re
from pathlib import Path
from typing import List

from config import TEMPLATE_DIR


EXAMPLE_TOPICS: List[str] = [
    "Non-Disclosure Agreement",
    "Mutual Non-Disclosure Agreement",
    "Employment Agreement",
    "Independent Contractor Agreement",
    "Service Level Agreement",
    "Master Services Agreement",
    "Software License Agreement",
    "End User License Agreement",
    "Data Processing Addendum",
    "Privacy Policy",
    "Terms of Service",
    "Consulting Agreement",
    "Sales Agreement",
    "Purchase Agreement",
    "Lease Agreement",
    "Rental Agreement",
    "Partnership Agreement",
    "Shareholders Agreement",
    "Founders Agreement",
    "Loan Agreement",
    "Promissory Note",
    "Letter of Intent",
    "Memorandum of Understanding",
    "Franchise Agreement",
    "Agency Agreement",
    "Distribution Agreement",
    "Reseller Agreement",
    "Non-Compete Agreement",
    "Non-Solicitation Agreement",
    "IP Assignment Agreement",
    "Work for Hire Agreement",
    "SaaS Agreement",
    "Website Terms of Use",
    "Cookie Policy",
    "Acceptable Use Policy",
    "Return and Refund Policy",
    "Warranty Policy",
    "Arbitration Agreement",
    "Settlement Agreement",
    "Release of Claims",
    "Joint Venture Agreement",
    "Asset Purchase Agreement",
    "Stock Purchase Agreement",
    "Consulting SOW",
    "Professional Services SOW",
    "Change Order",
    "Employment Offer Letter",
    "Employee Handbook Acknowledgment",
    "Commission Agreement",
    "Severance Agreement",
    "Termination Notice",
    "Demand Letter",
    "Cease and Desist Letter",
    "DMCA Takedown Notice",
    "Trademark License",
    "Patent License",
    "Copyright License",
    "Open Source License Notice",
    "At-Will Employment Notice",
    "Internship Agreement",
    "Volunteer Agreement",
    "Confidentiality Policy",
    "Security Policy",
    "DPA Annex: Subprocessors",
    "GDPR Data Subject Request Form",
    "CCPA Notice",
    "HIPAA BAA",
    "FERPA Consent",
    "Joint Controller Agreement",
    "Standard Contractual Clauses",
    "International Data Transfer Addendum",
    "Marketing Consent Form",
    "Photo/Video Release",
    "Event Waiver",
    "Media NDA",
    "Talent Release",
    "Influencer Agreement",
    "Affiliate Agreement",
    "Referral Agreement",
    "Managed Services Agreement",
    "Support and Maintenance Policy",
    "Uptime SLA",
    "Bug Bounty Policy",
    "Incident Response Policy",
    "Business Continuity Plan Acknowledgment",
    "Subcontractor Agreement",
    "Supplier Agreement",
    "Manufacturing Agreement",
    "Quality Assurance Agreement",
    "Non-Circumvention Agreement",
    "Loan Security Agreement",
    "Guaranty Agreement",
    "Board Consent",
    "Shareholder Consent",
    "Bylaws",
    "Operating Agreement",
    "Certificate of Incorporation",
    "ESOP Plan Summary",
    "Stock Option Grant Notice",
    "Advisor Agreement",
    "Consulting Confidentiality Rider",
    "Export Compliance Policy",
    "KYC Questionnaire",
    "AML Policy",
    "Whistleblower Policy",
]


TEMPLATE_BODY = (
    "This is a sample {title}.\n\n"
    "Purpose: Provide a baseline legal template for {title} usage.\n\n"
    "Key Sections:\n"
    "1. Parties and Definitions\n"
    "2. Term and Termination\n"
    "3. Confidentiality and IP\n"
    "4. Payment and Consideration (if applicable)\n"
    "5. Warranties and Disclaimers\n"
    "6. Limitation of Liability\n"
    "7. Governing Law and Dispute Resolution\n\n"
    "Notes: Replace placeholders with actual party names, dates, and terms."
)


def ensure_templates(folder: str, num: int = 100) -> None:
    Path(folder).mkdir(parents=True, exist_ok=True)
    existing = list(Path(folder).glob("*.txt"))

    if len(existing) >= num:
        print(f"Found {len(existing)} templates; no generation needed.")
        return

    topics = EXAMPLE_TOPICS.copy()
    # Repeat topics to reach 'num'
    while len(topics) < num:
        topics.extend(EXAMPLE_TOPICS)
    topics = topics[:num]

    created = 0
    for idx, title in enumerate(topics, start=1):
        safe_title = re.sub(r"[^a-z0-9_]+", "_", title.lower().replace(" ", "_"))
        filename = f"{idx:03d}_" + safe_title + ".txt"
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(TEMPLATE_BODY.format(title=title))
            created += 1

    print(f"Created {created} new templates in {folder}")


if __name__ == "__main__":
    ensure_templates(TEMPLATE_DIR, 100)


