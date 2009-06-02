/* 
 * More info at: http://phpjs.org
 * 
 * This is version: 2.67
 * php.js is copyright 2009 Kevin van Zonneveld.
 * 
 * Portions copyright Brett Zamir (http://brett-zamir.me), Kevin van Zonneveld
 * (http://kevin.vanzonneveld.net), Onno Marsman, Michael White
 * (http://getsprink.com), Waldo Malqui Silva, Paulo Ricardo F. Santos, Jack,
 * Jonas Raoni Soares Silva (http://www.jsfromhell.com), Philip Peterson, Ates
 * Goral (http://magnetiq.com), Legaev Andrey, Martijn Wieringa, Nate,
 * Philippe Baumann, Enrique Gonzalez, Webtoolkit.info
 * (http://www.webtoolkit.info/), Theriault, travc, Jani Hartikainen, Carlos
 * R. L. Rodrigues (http://www.jsfromhell.com), Ash Searle
 * (http://hexmen.com/blog/), Ole Vrijenhoek, stag019, Erkekjetter, Andrea
 * Giammarchi (http://webreflection.blogspot.com), d3x, marrtins, Johnny Mast
 * (http://www.phpvrouwen.nl), Alex, GeekFG (http://geekfg.blogspot.com),
 * Michael Grier, Steve Hilder, Oleg Eremeev, Steven Levithan
 * (http://blog.stevenlevithan.com), gorthaur, David, gettimeofday, Arpad Ray
 * (mailto:arpad@php.net), Public Domain (http://www.json.org/json2.js),
 * Pellentesque Malesuada, Mirek Slugen, Caio Ariede (http://caioariede.com),
 * Tyler Akins (http://rumkin.com), KELAN, Alfonso Jimenez
 * (http://www.alfonsojimenez.com), Marc Palau, Lars Fischer, AJ, Thunder.m,
 * Breaking Par Consulting Inc
 * (http://www.breakingpar.com/bkp/home.nsf/0/87256B280015193F87256CFB006C45F7),
 * Josh Fraser
 * (http://onlineaspect.com/2007/06/08/auto-detect-a-time-zone-with-javascript/),
 * mdsjack (http://www.mdsjack.bo.it), Karol Kowalski, Aman Gupta, Sakimori,
 * kenneth, Paul, Ole Vrijenhoek (http://www.nervous.nl/), T. Wild, Hyam
 * Singer (http://www.impact-computing.com/), Douglas Crockford
 * (http://javascript.crockford.com), Steve Clay, john
 * (http://www.jd-tech.net), ger, marc andreu, nobbler, mktime, madipta, David
 * James, class_exists, noname, Marco, Brad Touesnard, J A R, djmix, Lincoln
 * Ramsay, Linuxworld, Thiago Mata (http://thiagomata.blog.com), Pyerre, Jon
 * Hohle, Bayron Guevara, duncan, Sanjoy Roy, sankai, 0m3r, Felix
 * Geisendoerfer (http://www.debuggable.com/felix), Gilbert, Subhasis Deb,
 * Soren Hansen, T0bsn, Eugene Bulkin (http://doubleaw.com/), Der Simon
 * (http://innerdom.sourceforge.net/), JB, LH, Marc Jansen, Francesco, echo is
 * bad, XoraX (http://www.xorax.info), MeEtc (http://yass.meetcweb.com),
 * Peter-Paul Koch (http://www.quirksmode.org/js/beat.html), Nathan, Tim Wiel,
 * Ozh, David Randall, Bryan Elliott, Jalal Berrami, Arno, Kirk Strobeck,
 * Mick@el, rezna, Martin Pool, Pierre-Luc Paour, Jason Wong
 * (http://carrot.org/), Daniel Esteban, Saulo Vallory, Kristof Coomans
 * (SCK-CEN Belgian Nucleair Research Centre), Eric Nagel, Bobby Drake,
 * penutbutterjelly, Christian Doebler, setcookie, Gabriel Paderni, Simon
 * Willison (http://simonwillison.net), Pul, Luke Godfrey, Blues
 * (http://tech.bluesmoon.info/), Anton Ongson, Valentina De Rosa, Wagner B.
 * Soares, Yves Sucaet, sowberry, hitwork, johnrembo, Philippe Jausions
 * (http://pear.php.net/user/jausions), Nick Callen, ejsanders, Kankrelune
 * (http://www.webfaktory.info/), Aidan Lister (http://aidanlister.com/),
 * Norman "zEh" Fuchs, dptr1988, T.Wild, Alan C, uestla, strcasecmp, strcmp,
 * metjay, Pedro Tainha (http://www.pedrotainha.com), DxGx, Alexander Ermolaev
 * (http://snippets.dzone.com/user/AlexanderErmolaev), ChaosNo1, YUI Library:
 * http://developer.yahoo.com/yui/docs/YAHOO.util.DateLocale.html, Blues at
 * http://hacks.bluesmoon.info/strftime/strftime.js, taith, Robin, Matt
 * Bradley, Tim de Koning, Luis Salazar (http://www.freaky-media.com/),
 * FGFEmperor, baris ozdil, Tod Gentille, FremyCompany, Manish, Cord, Slawomir
 * Kaniecki, ReverseSyntax, Mateusz "loonquawl" Zalega, Scott Cariss,
 * Francois, Victor, stensi, vlado houba, date, gabriel paderni, Yannoo,
 * mk.keck, Leslie Hoare, Ben Bryan, Dino, Andrej Pavlovic, Andreas, DtTvB
 * (http://dt.in.th/2008-09-16.string-length-in-bytes.html), Russell Walker,
 * Garagoth, booeyOH, Cagri Ekin, Benjamin Lupton, davook, Atli Þór, jakes,
 * Allan Jensen (http://www.winternet.no), Howard Yeend, Kheang Hok Chin
 * (http://www.distantia.ca/), Luke Smith (http://lucassmith.name), Rival,
 * Diogo Resende
 * 
 * Dual licensed under the MIT (MIT-LICENSE.txt)
 * and GPL (GPL-LICENSE.txt) licenses.
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL KEVIN VAN ZONNEVELD BE LIABLE FOR ANY CLAIM, DAMAGES
 * OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 * ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */ 


function get_html_translation_table(table, quote_style) {
    // Returns the internal translation table used by htmlspecialchars and htmlentities  
    // 
    // version: 905.3122
    // discuss at: http://phpjs.org/functions/get_html_translation_table
    // +   original by: Philip Peterson
    // +    revised by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // +   bugfixed by: noname
    // +   bugfixed by: Alex
    // +   bugfixed by: Marco
    // +   bugfixed by: madipta
    // +   improved by: KELAN
    // +   improved by: Brett Zamir (http://brett-zamir.me)
    // %          note: It has been decided that we're not going to add global
    // %          note: dependencies to php.js. Meaning the constants are not
    // %          note: real constants, but strings instead. integers are also supported if someone
    // %          note: chooses to create the constants themselves.
    // *     example 1: get_html_translation_table('HTML_SPECIALCHARS');
    // *     returns 1: {'"': '&quot;', '&': '&amp;', '<': '&lt;', '>': '&gt;'}
    
    var entities = {}, histogram = {}, decimal = 0, symbol = '';
    var constMappingTable = {}, constMappingQuoteStyle = {};
    var useTable = {}, useQuoteStyle = {};
    
    // Translate arguments
    constMappingTable[0]      = 'HTML_SPECIALCHARS';
    constMappingTable[1]      = 'HTML_ENTITIES';
    constMappingQuoteStyle[0] = 'ENT_NOQUOTES';
    constMappingQuoteStyle[2] = 'ENT_COMPAT';
    constMappingQuoteStyle[3] = 'ENT_QUOTES';

    useTable       = !isNaN(table) ? constMappingTable[table] : table ? table.toUpperCase() : 'HTML_SPECIALCHARS';
    useQuoteStyle = !isNaN(quote_style) ? constMappingQuoteStyle[quote_style] : quote_style ? quote_style.toUpperCase() : 'ENT_COMPAT';

    if (useTable !== 'HTML_SPECIALCHARS' && useTable !== 'HTML_ENTITIES') {
        throw new Error("Table: "+useTable+' not supported');
        // return false;
    }

    // ascii decimals for better compatibility
    entities['38'] = '&amp;';
    if (useQuoteStyle !== 'ENT_NOQUOTES') {
        entities['34'] = '&quot;';
    }
    if (useQuoteStyle === 'ENT_QUOTES') {
        entities['39'] = '&#039;';
    }
    entities['60'] = '&lt;';
    entities['62'] = '&gt;';

    if (useTable === 'HTML_ENTITIES') {
        entities['160'] = '&nbsp;';
        entities['161'] = '&iexcl;';
        entities['162'] = '&cent;';
        entities['163'] = '&pound;';
        entities['164'] = '&curren;';
        entities['165'] = '&yen;';
        entities['166'] = '&brvbar;';
        entities['167'] = '&sect;';
        entities['168'] = '&uml;';
        entities['169'] = '&copy;';
        entities['170'] = '&ordf;';
        entities['171'] = '&laquo;';
        entities['172'] = '&not;';
        entities['173'] = '&shy;';
        entities['174'] = '&reg;';
        entities['175'] = '&macr;';
        entities['176'] = '&deg;';
        entities['177'] = '&plusmn;';
        entities['178'] = '&sup2;';
        entities['179'] = '&sup3;';
        entities['180'] = '&acute;';
        entities['181'] = '&micro;';
        entities['182'] = '&para;';
        entities['183'] = '&middot;';
        entities['184'] = '&cedil;';
        entities['185'] = '&sup1;';
        entities['186'] = '&ordm;';
        entities['187'] = '&raquo;';
        entities['188'] = '&frac14;';
        entities['189'] = '&frac12;';
        entities['190'] = '&frac34;';
        entities['191'] = '&iquest;';
        entities['192'] = '&Agrave;';
        entities['193'] = '&Aacute;';
        entities['194'] = '&Acirc;';
        entities['195'] = '&Atilde;';
        entities['196'] = '&Auml;';
        entities['197'] = '&Aring;';
        entities['198'] = '&AElig;';
        entities['199'] = '&Ccedil;';
        entities['200'] = '&Egrave;';
        entities['201'] = '&Eacute;';
        entities['202'] = '&Ecirc;';
        entities['203'] = '&Euml;';
        entities['204'] = '&Igrave;';
        entities['205'] = '&Iacute;';
        entities['206'] = '&Icirc;';
        entities['207'] = '&Iuml;';
        entities['208'] = '&ETH;';
        entities['209'] = '&Ntilde;';
        entities['210'] = '&Ograve;';
        entities['211'] = '&Oacute;';
        entities['212'] = '&Ocirc;';
        entities['213'] = '&Otilde;';
        entities['214'] = '&Ouml;';
        entities['215'] = '&times;';
        entities['216'] = '&Oslash;';
        entities['217'] = '&Ugrave;';
        entities['218'] = '&Uacute;';
        entities['219'] = '&Ucirc;';
        entities['220'] = '&Uuml;';
        entities['221'] = '&Yacute;';
        entities['222'] = '&THORN;';
        entities['223'] = '&szlig;';
        entities['224'] = '&agrave;';
        entities['225'] = '&aacute;';
        entities['226'] = '&acirc;';
        entities['227'] = '&atilde;';
        entities['228'] = '&auml;';
        entities['229'] = '&aring;';
        entities['230'] = '&aelig;';
        entities['231'] = '&ccedil;';
        entities['232'] = '&egrave;';
        entities['233'] = '&eacute;';
        entities['234'] = '&ecirc;';
        entities['235'] = '&euml;';
        entities['236'] = '&igrave;';
        entities['237'] = '&iacute;';
        entities['238'] = '&icirc;';
        entities['239'] = '&iuml;';
        entities['240'] = '&eth;';
        entities['241'] = '&ntilde;';
        entities['242'] = '&ograve;';
        entities['243'] = '&oacute;';
        entities['244'] = '&ocirc;';
        entities['245'] = '&otilde;';
        entities['246'] = '&ouml;';
        entities['247'] = '&divide;';
        entities['248'] = '&oslash;';
        entities['249'] = '&ugrave;';
        entities['250'] = '&uacute;';
        entities['251'] = '&ucirc;';
        entities['252'] = '&uuml;';
        entities['253'] = '&yacute;';
        entities['254'] = '&thorn;';
        entities['255'] = '&yuml;';
    }
    
    // ascii decimals to real symbols
    for (decimal in entities) {
        symbol = String.fromCharCode(decimal);
        histogram[symbol] = entities[decimal];
    }
    
    return histogram;
}

function htmlentities (string, quote_style) {
    // Convert all applicable characters to HTML entities  
    // 
    // version: 905.1002
    // discuss at: http://phpjs.org/functions/htmlentities
    // +   original by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // +    revised by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // +   improved by: nobbler
    // +    tweaked by: Jack
    // +   bugfixed by: Onno Marsman
    // +    revised by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // -    depends on: get_html_translation_table
    // *     example 1: htmlentities('Kevin & van Zonneveld');
    // *     returns 1: 'Kevin &amp; van Zonneveld'
    // *     example 2: htmlentities("foo'bar","ENT_QUOTES");
    // *     returns 2: 'foo&#039;bar'
    var histogram = {}, symbol = '', tmp_str = '', entity = '';
    tmp_str = string.toString();
    
    if (false === (histogram = this.get_html_translation_table('HTML_ENTITIES', quote_style))) {
        return false;
    }
    
    for (symbol in histogram) {
        entity = histogram[symbol];
        tmp_str = tmp_str.split(symbol).join(entity);
    }
    
    return tmp_str;
}
