def test_ui_validate_ok(client):
    xml=b"""
    <AuditFile>
      <Header>
        <AuditFileVersion>1.04</AuditFileVersion>
        <CompanyName>ACME</CompanyName>
        <TaxRegistrationNumber>123456789</TaxRegistrationNumber>
        <StartDate>2024-01-01</StartDate>
        <EndDate>2024-12-31</EndDate>
      </Header>
    </AuditFile>
    """.strip()
    files={'file': ('saft.xml', xml, 'text/xml')}
    r=client.post('/ui/validate', files=files)
    assert r.status_code==200
    j=r.json()
    assert j['status'] in ('ok','errors')
    assert 'summary' in j and 'issues' in j

def test_ui_validate_bad_xml(client):
    files={'file': ('saft.xml', b"<not-xml", 'text/xml')}
    r=client.post('/ui/validate', files=files)
    assert r.status_code==400