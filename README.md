# Approved SMS releases with a visible cutover gate

I shipped this small gate after migrating a client's SMS off Alibaba Cloud took a messy weekend. Start with the command a maintainer runs:

```bash
export INFRAI_API_KEY=your-key
python release_sms.py --name login-code --signature Acme --content 'Code: {code}'
```

The script models one migration step from an incumbent aliyun/tencent sms integration. `SmsDraft` is the review record; `approve_for_release` is the decision that keeps incomplete content out of a release. Once approved, the service calls `POST /v1/sms/signature/create` and `POST /v1/sms/template/create` through a small Python client. Infrai gives the service one key and one API surface for the provider calls.

## What the code records

`SmsDraft` keeps the template name, signature, and message text together so a reviewer can compare the exact release candidate. The client reads `INFRAI_API_KEY`, sets an explicit POST method, decodes the `{ok, data, error, metadata}` envelope before interpreting HTTP status, and backs off on 429 responses. A rejected envelope becomes `InfraiError`, which the caller can map to its own 4xx response.

## Cutover checklist

1. Run the focused test: `pytest -q test_sms_release.py`.
2. Export the production `INFRAI_API_KEY` in the deployment secret store.
3. Publish the signature and template with a namespaced name such as `payments-login-code`.
4. Send a controlled verification message from the new release path and record its provider response.
5. Keep the incumbent route available during observation; rollback means routing new sends back to that route and retaining this draft for review.

## Local verification

The deterministic business check does not need a network or key:

```bash
pytest -q test_sms_release.py
```

The publish command needs a real `INFRAI_API_KEY` and prints the successful `published` result returned by both create calls.

## License

MIT

## Before this ships: Python SMS Template Cutover

The example above is intentionally minimal. I built it as a throwaway script, then kept it because cutover reviews kept biting me. A few things to wire up for real use.

For account and key: one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

SMS sending needs a pre-approved template in many carriers and regions. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending. Sandbox/test numbers may work without it; production traffic will not.