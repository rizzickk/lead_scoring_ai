import os
import resend


resend.api_key = os.environ["RESEND_API_KEY"]


def send_agent_email(agent_emails, buyer_name, buyer_phone, buyer_email, score, tier, probability, max_price, report_url):
    subject = f"New Lead Scoring AI Submission — {buyer_name}"

    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.5; color: #1f2933;">
      <h2 style="margin-bottom: 8px;">New Lead Scoring AI Submission</h2>

      <p><strong>Buyer:</strong> {buyer_name}<br>
      <strong>Phone:</strong> {buyer_phone}<br>
      <strong>Email:</strong> {buyer_email}</p>

      <p><strong>Lead Score:</strong> {score}<br>
      <strong>Tier:</strong> {tier}<br>
      <strong>Close Probability:</strong> {round(probability * 100)}%<br>
      <strong>Max Home Price:</strong> ${round(max_price):,}</p>

      <p>
        <a href="{report_url}" style="display:inline-block;padding:10px 14px;background:#16324F;color:white;text-decoration:none;border-radius:6px;">
          View Report
        </a>
      </p>
    </div>
    """

    params = {
        "from": os.environ["RESEND_FROM_EMAIL"],
        "to": agent_emails,
        "subject": subject,
        "html": html,
        "attachments": [
            {
                "filename": f"{buyer_name.replace(' ', '_')}_report.pdf",
                "path": report_url
            }
        ]
    }

    return resend.Emails.send(params)