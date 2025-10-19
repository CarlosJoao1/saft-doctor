def test_pt_flow(client):
    # register + login
    client.post('/auth/register', json={'username':'alice','password':'secret'})
    r=client.post('/auth/token', data={'username':'alice','password':'secret'})
    token=r.json()['access_token']; h={'Authorization': f'Bearer {token}'}
    # save AT creds
    r=client.post('/pt/secrets/at', json={'username':'NIF','password':'PASS'}, headers=h)
    assert r.status_code==200
    # upload + submit (expect 502 due to missing JAR)
    files={'file': ('saft.xml', b'<AuditFile></AuditFile>', 'text/xml')}
    r=client.post('/pt/files/upload', files=files, headers=h)
    key=r.json()['object']
    r=client.post(f'/pt/submit?object_key={key}', headers=h)
    assert r.status_code==502 and 'FACTEMICLI.jar' in r.json()['detail']
