var runningRequest = false;
var request;

$(document).ready(function() {
	$.preloadCssImages();
	$('.search_box').inputHint('inputhint');
	$('#q').keyup(function(e) {
		if ($(this).val().length > 2) {
			$(this).removeClass('results').removeClass('no_results').addClass('loading');
			e.preventDefault();
			$q = $(this);
			get_results($q.val());
		} else {
			$(this).removeClass('results').removeClass('no_results').removeClass('loading');
		}
	});

	$('#share_email').click(function(e) {
		e.preventDefault();
		share_email();
	});
	
	check_desktop();
	
	/*
	$('#intro_open').click(function() {
		$('.intro_link').hide();
		$('.intro').show();
	});
	*/
});

function share_email() {
	name = prompt('What is your name?');
	email = prompt('Email address you would like to share this page with?');
	
	$.post("/lib/email.api.php", { name: name, email: email },
		function(data) {
			alert("Data Loaded: " + data);
		});
}

function get_results(q) {
	/*
	 * Get the search results from the API and display them
	*/
	//var api_url = '/lib/search.api.php';
//    var api_url = '/ajax/nodes_json';
    var api_url = '/api/nodes/search';
	$q = $('#q');
	
	if(runningRequest){
		request.abort();
	}
	      
	runningRequest = true;

	request = $.getJSON(api_url, {s:q}, function(data) {
		var items = [];
		
		$.each(data, function(i, item) {
			id = item.id;
			name = item.name;
			name_url = encodeURIComponent(name.toLowerCase().replace(/ /g, '-'));
			
			items.push('<li id="resource-' + id + '"><a href="/tag/' + id + '/' + name_url + '/">' + name + '</a></li>');
			 
			runningRequest = false;
		});
		
		$('ul.search_results').remove();
		
		$('<ul/>', {
			'class': 'search_results',
			html: items.join('')
		}).appendTo('#page_wrap');
		
		$q.removeClass('loading');
		if (data.length > 0) {
			$q.addClass('results');
			/* Hide intro box & show the open link instead */
			$('.intro').hide();
			//$('.intro_link').show();
		} else {
			$q.addClass('no_results');
		}
	});
}

function check_desktop() {
	/*
	 * Simple function to make the mobile site display better natively on a desktop browser
	*/
	
	if (screen.width > 699) {
		$('html').css({'max-width':'480px'});
	}
}

function validate_email(email){
   var emailPattern = /^[a-zA-Z0-9.\+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
   return emailPattern.test(email);
 }


/* Cookies */
function set_cookie(name,value,days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    document.cookie = name+"="+value+expires+"; path=/";
}

function get_cookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function delete_cookie(name) {
    setCookie(name,"",-1);
}
