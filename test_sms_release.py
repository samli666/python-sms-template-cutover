from infrai_sms import InfraiSms, SmsDraft, approve_for_release


def test_release_requires_complete_approval_record():
    assert approve_for_release(SmsDraft("login-code", "Acme", "Code: {code}")) is True
    assert approve_for_release(SmsDraft("", "Acme", "Code: {code}")) is False


def test_create_requests_include_required_fields():
    client = InfraiSms("test-key")
    requests = []
    client._post = lambda path, payload: requests.append((path, payload)) or {}
    draft = SmsDraft("login-code", "Acme", "Code: {code}")

    client.create_signature(draft)
    client.create_template(draft)

    assert requests == [
        ("/v1/sms/signature/create", {"name": "Acme"}),
        ("/v1/sms/template/create", {"name": "login-code", "body": "Code: {code}"}),
    ]
