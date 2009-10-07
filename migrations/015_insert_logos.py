from dmigrations.mysql import migrations as m

class CustomMigration(m.Migration):
    def __init__(self):
        sql_up = ["""
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\aes.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\aes.jpg' WHERE abbreviation = 'AES';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\ap.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\ap.jpg' WHERE abbreviation = 'AP';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\bmc.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\bmc.jpg' WHERE abbreviation = 'BMC';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\bt.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\bt.jpg' WHERE abbreviation = 'BT';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\c.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\c.jpg' WHERE abbreviation = 'C';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\cas.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\cas.jpg' WHERE abbreviation = 'CAS';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\ceda.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\ceda.jpg' WHERE abbreviation = 'CEDA';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\ci.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\ci.jpg' WHERE abbreviation = 'CI';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\com.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\com.jpg' WHERE abbreviation = 'COM';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\cpmt.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\cpmt.jpg' WHERE abbreviation = 'CPMT';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\cs.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\cs.jpg' WHERE abbreviation = 'CS';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\csc.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\csc.jpg' WHERE abbreviation = 'CSC';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\dei.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\dei.jpg' WHERE abbreviation = 'DEI';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\e.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\e.jpg' WHERE abbreviation = 'E';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\ed.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\ed.jpg' WHERE abbreviation = 'ED';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\emb.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\emb.jpg' WHERE abbreviation = 'EMB';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\emc.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\emc.jpg' WHERE abbreviation = 'EMC';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\grs.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\grs.jpg' WHERE abbreviation = 'GRS';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\ias.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\ias.jpg' WHERE abbreviation = 'IAS';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\iceo.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\iceo.jpg' WHERE abbreviation = 'ICEO';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\ie.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\ie.jpg' WHERE abbreviation = 'IE';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\im.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\im.jpg' WHERE abbreviation = 'IM';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\it.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\it.jpg' WHERE abbreviation = 'IT';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\its.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\its.jpg' WHERE abbreviation = 'ITS';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\mag.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\mag.jpg' WHERE abbreviation = 'MAG';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\mtt.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\mtt.jpg' WHERE abbreviation = 'MTT';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\nano.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\nano.jpg' WHERE abbreviation = 'NANO';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\oe.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\oe.jpg' WHERE abbreviation = 'OE';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\pc.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\pc.jpg' WHERE abbreviation = 'PC';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\pe.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\pe.jpg' WHERE abbreviation = 'PE';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\pel.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\pel.jpg' WHERE abbreviation = 'PEL';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\pse.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\pse.jpg' WHERE abbreviation = 'PSE';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\r.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\r.jpg' WHERE abbreviation = 'R';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\ra.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\ra.jpg' WHERE abbreviation = 'RA';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\smc.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\smc.jpg' WHERE abbreviation = 'SMC';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\ssc.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\ssc.jpg' WHERE abbreviation = 'SSC';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\sys.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\sys.jpg' WHERE abbreviation = 'SYS';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\tmc.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\tmc.jpg' WHERE abbreviation = 'TMC';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\uffc.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\uffc.jpg' WHERE abbreviation = 'UFFC';
            UPDATE ieeetags_society SET logo_thumbnail = 'images\\\\sc_logos\\\\thumbnail\\\\vt.jpg', logo_full = 'images\\\\sc_logos\\\\full\\\\vt.jpg' WHERE abbreviation = 'VT';
        """]
        sql_down = ["""
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'AES';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'AP';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'BMC';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'BT';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'C';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'CAS';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'CEDA';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'CI';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'COM';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'CPMT';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'CS';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'CSC';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'DEI';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'E';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'ED';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'EMB';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'EMC';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'GRS';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'IAS';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'ICEO';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'IE';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'IM';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'IT';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'ITS';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'MAG';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'MTT';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'NANO';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'OE';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'PC';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'PE';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'PEL';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'PSE';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'R';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'RA';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'SMC';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'SSC';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'SYS';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'TMC';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'UFFC';
            UPDATE ieeetags_society SET logo_thumbnail = '', logo_full = '' WHERE abbreviation = 'VT';
        """]
        super(CustomMigration, self).__init__(
            sql_up=sql_up, sql_down=sql_down
        )
    # Or override the up() and down() methods

migration = CustomMigration()
