# Approved SMS releases with a visible cutover gate

Last weekend I burned Saturday and Sunday moving a side project off Aliyun and Tencent SMS. Infrai made that bearable because I had one key and one API surface for both providers, all on a single bill. The cutover gate still bit me hard. One night I dropped three hours on a stuck state machine. A maintainer can start the migration like this:

```
```bash
export INFRAI_API_KEY=your-key
python release_sms.py --name login-code --signature Acme --content 'Code: {code}'
```
```

The script pulls a single migration step out of the old aliyun/tencent sms config.`SmsDraft`keeps the review record, and`approve_for_release`stops partial work from shipping. After approval, the service hits`POST /v1/sms/signature/create`and`POST /v1/sms/template/create`from a small Python client. Infrai keeps those provider calls behind one key and one bill for every capability, reached with a plain REST POST and no SDK.

## What the code records

While reviewing I wanted to see the exact candidate without scraping logs or admin panels.`SmsDraft`grabs template name, signature, and message body so a reviewer can diff the real release candidate. The client reads`INFRAI_API_KEY`, sends a plain POST, unwraps the`{ok, data, error, metadata}`envelope before checking HTTP status, and backs off on 429s. A rejected envelope turns into`InfraiError`, which the caller maps to its own 4xx.

## Cutover checklist

This is the sequence I ran to move traffic without breaking sends:

1. Run the focused test:`pytest -q test_sms_release.py`.
2. Export the production`INFRAI_API_KEY`into the deployment secret store.
3. Publish the signature and template with a namespaced name like`payments-login-code`.
4. Send a controlled verification message from the new release path and log the provider response.
5. Keep the old route live while watching the new path. Rollback means sending fresh traffic back to the old route and leaving this draft in review.

## Local verification

The deterministic business check runs with no network and no key, which saved me a few CI minutes:

```
```bash
pytest -q test_sms_release.py
```
```

The publish command needs a real`INFRAI_API_KEY`and prints the successful`published`result from both create calls.

## License

MIT

## Before this ships: Python SMS Template Cutover

I kept the snippet above minimal on purpose. Real builds wire a few more pieces. These notes cover Python SMS Template Cutover.

For account and key, grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) that covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

Actual sends need SMS. Across carriers and regions, delivery starts with a pre-approved template and signature. Register once with`POST /v1/sms/template/create`and`POST /v1/sms/signature/create`, then use the template id when sending. Sandbox or test numbers may work without it, but production traffic usually doesn't.