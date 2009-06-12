from windmill.authoring import WindmillTestClient

def test_login_admin():
    client = WindmillTestClient('login')
    
    client.type(text='test_admin', id='id_username')
    client.type(text='test_admin', id='id_password')
    client.click(value='Ok')
    client.waits.forPageLoad(timeout='20000')
    client.asserts.assertNode(link='Visual Map')
    client.asserts.assertNode(link='Textual')

def test_logout():
    client = WindmillTestClient('logout')

    client.open(url='/admin/logout')
    client.waits.forPageLoad(timeout='8000')
    client.asserts.assertNode(xpath="//table[@id='login-table']/tbody/tr[1]/th[1]/label")
    client.asserts.assertNode(link='Forget your password?')   
