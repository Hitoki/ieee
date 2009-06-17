from windmill.authoring import WindmillTestClient

def test_frontend_enabled():
    client = WindmillTestClient('frontend_enabled')

    client.open(url='/admin/logout')
    client.waits.forPageLoad(timeout='8000')
    client.asserts.assertNode(xpath="//table[@id='login-table']/tbody/tr[1]/th[1]/label")

def test_roamer_page():
    client = WindmillTestClient('test_roamer_page')
    
    client.open(url='/roamer')
    client.waits.forPageLoad(timeout='8000')
    client.asserts.assertNode(id='constellation-roamer-embed')

def test_tags_page():
    client = WindmillTestClient('test_tags_page')

    client.open(url='/textui_help')
    client.waits.forPageLoad(timeout='8000')
    client.click(link='Continue to the Tags Interface...')
    client.waits.forPageLoad(timeout='20000')
    client.asserts.assertNode(id='tags')

def test_admin_home_page():
    client = WindmillTestClient('test_admin_home_page')

    client.open(url='/admin/')
    client.waits.forPageLoad(timeout='8000')
    client.asserts.assertText(xpath='/html/body/table/tbody/tr[1]/td[2]/div[2]/h1', validator='Admin Home')

def test_manage_society_page():
    client = WindmillTestClient('test_manage_society_page')

    client.open(url='/admin/society/1/manage')
    client.waits.forPageLoad(timeout='8000')
    client.asserts.assertNode(link="Manage this Society's Resources.+")
