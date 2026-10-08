from __future__ import annotations

import argparse
import json

from infrai_sms import InfraiSms, SmsDraft, approve_for_release


def publish(draft: SmsDraft) -> dict[str, object]:
    if not approve_for_release(draft):
        return {"status": "blocked", "reason": "approval fields are required"}
    client = InfraiSms()
    signature = client.create_signature(draft)
    template = client.create_template(draft)
    return {"status": "published", "signature": signature, "template": template}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish one approved SMS pair")
    parser.add_argument("--name", required=True)
    parser.add_argument("--signature", required=True)
    parser.add_argument("--content", required=True)
    args = parser.parse_args()
    print(json.dumps(publish(SmsDraft(args.name, args.signature, args.content)), indent=2))
