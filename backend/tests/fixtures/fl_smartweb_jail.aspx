
<meta http-equiv="X-UA-Compatible" content="IE=8"/>
<!doctype html >
<!--<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">-->
<html xmlns="http://www.w3.org/1999/xhtml">
<head id="Head1">
	<style type="text/css">
		.InmateInfoGridTd
		{
			white-space: nowrap;
            text-space-collapse:collapse;
            column-gap: 0px;
			/*width: auto;*/
		}
	</style>
	<title>
	JAIL View
</title><link id="SiteCSS" rel="stylesheet" type="text/css" href="MainSO.css" /><link href="Print.css" rel="stylesheet" type="text/css" media="print" />
	<script type="text/javascript" language="javascript" src="js/Main.js"></script>
	<script type="text/javascript" language="javascript" src="js/jquery_1_9_1.js"></script>
	<script type="text/javascript">

	    var SearchVals = { FirstName: '', MiddleName: '', LastName: '', BeginBookDate: '', EndBookDate: '', BeginReleaseDate: '', EndReleaseDate: '', TypeJailSearch: 0, RecordsLoaded: 0, SortOption: 0, SortOrder: 0, IsDefault : true};

		function LoadMoreResults() {
		    $("#LoadMoreRow").hide();
		    $("#PrintRow").hide();
		    $("#upProgPnl").show();
			//if we haven't intialized this, then this is the first more results set loaded
			if (SearchVals.RecordsLoaded == 0)
				SearchVals.RecordsLoaded = parseInt($("#ResultsReturned").text());

			$.ajax({
				type: "POST",
				url: "Jail.aspx/AddMoreResults",
				data: JSON.stringify(SearchVals),
				contentType: "application/json; charset=utf-8",
				dataType: "json",
				success: function (msg) {
					var data = msg.d.Data;
					var jailInfoDiv = $("#JailInfo").children().children().first();
					if (data.resultsReturned > 0) {
					    jailInfoDiv.html(jailInfoDiv.html() + data.data);
						SearchVals.RecordsLoaded += data.resultsReturned;
						$("#lbGridInfo").text("Number of Inmate Records Returned: " + SearchVals.RecordsLoaded);

						//we've hit the end of the results
						if (data.resultsAttempted > data.resultsReturned)
						    $("#LoadMoreRow").hide();
						else
						    $("#LoadMoreRow").show();
					}
					else {
							$("#LoadMoreRow").hide();
					}

					
					$("#upProgPnl").hide();
					$("#PrintRow").show();
				}
			});
		}

		function LoadMoreMouseEnter() {
		    $("#LoadMoreRow").css('background-color', 'rgb(192, 192, 192)');
		}

		function LoadMoreMouseLeave() {
		    $("#LoadMoreRow").css('background-color', 'rgb(224, 224, 224)');
		}


		function SearchTypeSelect() {
			var searchTypeDropDown = document.getElementById('TypeSearch');
			var selected = searchTypeDropDown.options[searchTypeDropDown.selectedIndex].value;
			var ReleaseBeginInput = document.getElementById('tbBeginReleaseDate');
			var ReleaseBeginLabel = document.getElementById('BeginReleaseDateLabel');
			var ReleaseEndInput = document.getElementById('tbEndReleaseDate');
			var ReleaseEndLabel = document.getElementById('EndReleaseDateLabel');
			switch (selected) {
				case "0":
					ReleaseBeginInput.style.display = "none";
					ReleaseBeginInput.value = '';
					ReleaseEndInput.style.display = "none";
					ReleaseEndInput.value = '';
					ReleaseBeginLabel.style.display = "none";
					ReleaseEndLabel.style.display = "none";
					break;
				case "1":
					ReleaseBeginInput.style.display = "block";
					ReleaseEndInput.style.display = "block";
					ReleaseBeginLabel.style.display = "block";
					ReleaseEndLabel.style.display = "block";
					break;
				case "2":
					ReleaseBeginInput.style.display = "block";
					ReleaseEndInput.style.display = "block";
					ReleaseBeginLabel.style.display = "block";
					ReleaseEndLabel.style.display = "block";
					break;
			}
		}
		//takes the onclick from an expander element and expands the expanded element (or folds depending on the state)
		function ToggleExpand(expanderID) {
			var expandedID = "expanded" + expanderID.replace("expander", "");
			//They are spelt similarly to keep you on your toes.
			var expanderElement = document.getElementById(expanderID);
			var expandedElement = document.getElementById(expandedID);

			//toggle logic
			if (expandedElement.style.display == "none") {
				expandedElement.style.display = "table-cell";
				expanderElement.innerHTML = "[-]";
			}
			else {
				expandedElement.style.display = "none";
				expanderElement.innerHTML = "[+]";
			}
		}
		function printFrame(){
		    this.focus();
		    this.print();
		}
		
		function PrintPreview() {
		    if (SearchVals.RecordsLoaded == 0)
		        SearchVals.RecordsLoaded = parseInt($("#ResultsReturned").text());
		    var url = "Jail.aspx?preview=true&searchvalues=" + JSON.stringify(SearchVals);
		    var win = window.open(url, "_blank");
		    win.focus();
		}
	</script>
<link href="/SmartWEBClient/WebResource.axd?d=q9I-yWXtV0PxPTAOUEHr6ubNvt1mPOWERnItkhvUj47dl_KCGEj46eoKRxq1RqfHR9uinA8CpL8NEPHqs5ENpgV5w_bfGV3YuVxd2IVD00foMRFBEkz5lfEqUCpa5vgCwB52y9T6RkjSvde3G_fJgvsn0fycZ0XI3cFYPU4TJ_w1&amp;t=637933974820000000" type="text/css" rel="stylesheet" /><link href="/SmartWEBClient/WebResource.axd?d=VofeIBuW8cHdpwZliY_Lbi-CRImoO-aUZnVPI4KZlaSx-WPCd4-OmsWQ4c-hWIQbNt2HAxUx-9aQKjmEa8XtRt8AB4WDQSbUYXjYenxyj_syysJEDhn2AG2MZ4APSLqciezY2YKYtKlyuyNtX3ZpKMVYgv83kT0U1YvlNqlfkpM1&amp;t=637933974820000000" type="text/css" rel="stylesheet" /></head>
<body >
	<form name="form1" method="post" action="./jail.aspx" onsubmit="javascript:return WebForm_OnSubmit();" id="form1">
<div>
<input type="hidden" name="__EVENTTARGET" id="__EVENTTARGET" value="" />
<input type="hidden" name="__EVENTARGUMENT" id="__EVENTARGUMENT" value="" />
<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="/wEPDwUKMjAyNDQzNDg4Mg9kFgICAQ9kFgICAg8WAh4EaHJlZgUKTWFpblNPLmNzc2RkYFZHcCai3jqUPZ+MSxFd24Z0QjS3ij/ALUGYR3C8HfE=" />
</div>

<script type="text/javascript">
//<![CDATA[
var theForm = document.forms['form1'];
if (!theForm) {
    theForm = document.form1;
}
function __doPostBack(eventTarget, eventArgument) {
    if (!theForm.onsubmit || (theForm.onsubmit() != false)) {
        theForm.__EVENTTARGET.value = eventTarget;
        theForm.__EVENTARGUMENT.value = eventArgument;
        theForm.submit();
    }
}
//]]>
</script>


<script src="/SmartWEBClient/WebResource.axd?d=ogSnci-0RVT4qHIBHlogmKRuwr8YfOGZ5YXH9N2R5xQnejI2KQ9GL3P3Oy6zHfXwybKzhrb4K5JNzLUYUTk2o7iEfr2_TVywf1J6a5wfDrw1&amp;t=639190689332169432" type="text/javascript"></script>


<script src="/SmartWEBClient/ScriptResource.axd?d=9wlS-yuXF7nx9OSHgUx1138ldZD_TjjeTWa_2oNqE4KcqoHNfWPsV68_O63xMxTN5i8yyJu8wM0qNTRwWN4sW0HGgecvoHmmBPJdJDx32VqYNzZITneGBAjuIKoLhA0HzuTXvvJaH5FcvqRYN62yxTvCYLmP9NjWns-T4hCf4ZU1&amp;t=ffffffffa5405632" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=a2XjWKPwMHvqXUC2c_bDbGRh3EjmozZHQwwB0LEjsPCI4Zj9L0ZAjgSwEFuMB1B4AevtiiInSZpzKK_E6fxKs8U4LP_4ce_5NHE_I4zxtXCIRhLvomvti8BSyTZR23VralQgFLyjeAaEHNIIvSeS51-n5wMutAINtkMyvl_48tY1&amp;t=ffffffffbec1863d" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=t33F202Aii5_uctM1ibD-eox9Nars80sCpJQ0zRpUUe0u16uftVXOci8yCQhXU6XSHUj7EyU-mOOhcIJkrM7X3AFXza1R2t_h-6CGGZJnM1FMhwzas9fnzMfGluVXl99IXzcOHG3OvRCBRoOTo-wQqq9RzVCIIk3ov0eGeIDFDdIboZotF3TDi23EuiVF6-q0&amp;t=ffffffffbec1863d" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=sR-0nVvdijXzcKeXJJVdAH_Z0MzPbQxbvcDjXXvYFtzQj5ZmnnWQ4yMuKhYpwXZ3RPl8MLCuBSr-HNJtryxpENKWeESLLmcf1EPr6MpQuNtDJLuInjMPzalU_fVeWuZ-isV6bdJBDw2Tl8HshyJwlg2&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=eLmOwqsiiNBmJolSWIJbI5V2t6L4FHR5pmFFW2jdQJhXkwA4H_FAHQa0KwvsxgOXAu-FAfmeVvy2TWdecsIwEC7uyNoxQ9Z9EABLjn2w7NVZNbm8gnRjive0w1_vbcGJ0&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=fduNxBxUb36iRH71GPSYY8GTibq3aWSXXw4icq2jlc5mF2yUz3-ei95kzYp1YJ7olL4naX4l3FaTHckP0H_Ykz62B1_hfvigEo2Xw1Y_0tc34kQ1ZH1a_Xy2U0L6AAXk0&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=1YLro_5y5vCPYoecqUDXCz8pXAqk3hym_76dpgPaJ60JSj0BG_O_cKdjLPzynLoKE5crl8HukfmMh2aUUbU_WvdtXcuqixNnWt_1aW4UCJ5bT3kOPpQwTKiuPSYRf_9r0&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=Nfru0sSKAMTG1fYWtJwbLjrLLvcHKk-SRshuW25eMyT2cytKrydF987xKIiFSXCmlB-TtsgXu4Dctn4jEqmZz9GSX3J6q9ZWsaWRChig8cZRwywTd8wD9E4pNVVohsqd0&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=GfQRTQhpVNGi5qkoEhmoGKdFH8Joz_xrxOadJapYkbJSMROndJg_6QT5N6ZiYB9WbRc3Ykq4Daua_tL31nW8GjOhlch8pgpmiaPEF7PqULrCqOfgWA5ej6CLHVti2UbwH65z_RhO_6EMPJTwB6m2pg2&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=7vEhiAEQ1cFSVa_2jCGQSGzWQJJCIvvNT6MiT9-swp-4dpTdDxt0NB-aYtdKrvwdPjkVFV5IqcBHk-Rs0tv4CnQSLNuacWr1LQz-SaBm4RuukLjmVr9MOOf4k7NWxO890&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=JdkN3l00MEz6KU_t5uyMLzTzge6Pm-K5qWAOaQ8-qMi7sbFPftfTqIZu2_2b2WpszBErJSq3PedEr0pP3NmtX6mnZ_P7JnXQ3131A7QSJJAO8fG6MQb461ngelACC4P40&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=cWKDeVDQTm64b5wAo9VV-gYaaO0IW1_8qfUubcJWuQEc4pxCyuzLFZ4cO8JgvR7mhYh5u28UPQxDRqCaQOKXicpZsRFlENBN1qf5bXINOnjRB_H1XPde3_5sGp1tLGJl0&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=1DcAt463ID0_pFPyPMKe_Eq8xMfg6eiERqd4T1IMOtHfMgYjTnFDA0z00hX7pEEPxUYGxCGg3C8DVnI2nJYiHOx2uA56LvkHrOGYAKkQyL8b6IoqXiWDgCf1Gfu6ohEq4aquCl0MnLPyDvdPD0STlA2&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=kGk2ccbijxkEWE8OUkM2rcIgZqo9ka3uZnP86RK7wN9n0xjPmr-bkTVdm0oTJy4zTbqar3fM4Jg6Fhuqumav-gqeElkiAsJjk1Ulznb_qn_FOIM-AhKCIeYoAWw0O54O0&amp;t=5e95cc64" type="text/javascript"></script>
<script src="/SmartWEBClient/ScriptResource.axd?d=XKNMdHZSLKOQ1TcFdeZL9JlaRPRW6Iua1-a_Vro5JwEahuNp_BaHaX1bmDjJzXKCycoff9JpP-L_15d1Unh4KlQtI9_c6sIPcFzNkFUMC3BLRNhfqg_pxjQ8-09b70RCCnjKBmEei0KWxWFvXfPSoQ2&amp;t=5e95cc64" type="text/javascript"></script>
<script type="text/javascript">
//<![CDATA[
var PageMethods = function() {
PageMethods.initializeBase(this);
this._timeout = 0;
this._userContext = null;
this._succeeded = null;
this._failed = null;
}
PageMethods.prototype = {
_get_path:function() {
 var p = this.get_path();
 if (p) return p;
 else return PageMethods._staticInstance.get_path();},
getRecordsToLoad:function(succeededCallback, failedCallback, userContext) {
return this._invoke(this._get_path(), 'getRecordsToLoad',false,{},succeededCallback,failedCallback,userContext); },
AddMoreResults:function(FirstName,MiddleName,LastName,BeginBookDate,EndBookDate,BeginReleaseDate,EndReleaseDate,TypeJailSearch,RecordsLoaded,SortOption,SortOrder,IsDefault,succeededCallback, failedCallback, userContext) {
return this._invoke(this._get_path(), 'AddMoreResults',false,{FirstName:FirstName,MiddleName:MiddleName,LastName:LastName,BeginBookDate:BeginBookDate,EndBookDate:EndBookDate,BeginReleaseDate:BeginReleaseDate,EndReleaseDate:EndReleaseDate,TypeJailSearch:TypeJailSearch,RecordsLoaded:RecordsLoaded,SortOption:SortOption,SortOrder:SortOrder,IsDefault:IsDefault},succeededCallback,failedCallback,userContext); }}
PageMethods.registerClass('PageMethods',Sys.Net.WebServiceProxy);
PageMethods._staticInstance = new PageMethods();
PageMethods.set_path = function(value) { PageMethods._staticInstance.set_path(value); }
PageMethods.get_path = function() { return PageMethods._staticInstance.get_path(); }
PageMethods.set_timeout = function(value) { PageMethods._staticInstance.set_timeout(value); }
PageMethods.get_timeout = function() { return PageMethods._staticInstance.get_timeout(); }
PageMethods.set_defaultUserContext = function(value) { PageMethods._staticInstance.set_defaultUserContext(value); }
PageMethods.get_defaultUserContext = function() { return PageMethods._staticInstance.get_defaultUserContext(); }
PageMethods.set_defaultSucceededCallback = function(value) { PageMethods._staticInstance.set_defaultSucceededCallback(value); }
PageMethods.get_defaultSucceededCallback = function() { return PageMethods._staticInstance.get_defaultSucceededCallback(); }
PageMethods.set_defaultFailedCallback = function(value) { PageMethods._staticInstance.set_defaultFailedCallback(value); }
PageMethods.get_defaultFailedCallback = function() { return PageMethods._staticInstance.get_defaultFailedCallback(); }
PageMethods.set_enableJsonp = function(value) { PageMethods._staticInstance.set_enableJsonp(value); }
PageMethods.get_enableJsonp = function() { return PageMethods._staticInstance.get_enableJsonp(); }
PageMethods.set_jsonpCallbackParameter = function(value) { PageMethods._staticInstance.set_jsonpCallbackParameter(value); }
PageMethods.get_jsonpCallbackParameter = function() { return PageMethods._staticInstance.get_jsonpCallbackParameter(); }
PageMethods.set_path("jail.aspx");
PageMethods.getRecordsToLoad= function(onSuccess,onFailed,userContext) {PageMethods._staticInstance.getRecordsToLoad(onSuccess,onFailed,userContext); }
PageMethods.AddMoreResults= function(FirstName,MiddleName,LastName,BeginBookDate,EndBookDate,BeginReleaseDate,EndReleaseDate,TypeJailSearch,RecordsLoaded,SortOption,SortOrder,IsDefault,onSuccess,onFailed,userContext) {PageMethods._staticInstance.AddMoreResults(FirstName,MiddleName,LastName,BeginBookDate,EndBookDate,BeginReleaseDate,EndReleaseDate,TypeJailSearch,RecordsLoaded,SortOption,SortOrder,IsDefault,onSuccess,onFailed,userContext); }
var gtc = Sys.Net.WebServiceProxy._generateTypedConstructor;
Type.registerNamespace('System.Web.Mvc');
if (typeof(System.Web.Mvc.JsonResult) === 'undefined') {
System.Web.Mvc.JsonResult=gtc("System.Web.Mvc.JsonResult");
System.Web.Mvc.JsonResult.registerClass('System.Web.Mvc.JsonResult');
}
function WebForm_OnSubmit() {
if (typeof(ValidatorOnSubmit) == "function" && ValidatorOnSubmit() == false) return false;
return true;
}
//]]>
</script>

<div>

	<input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="C8445BF0" />
	<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="/wEdABEyO9X3Auyy5hM3p3RMKFaJRG9+ljXShLjYxWLx290v8NluaX2nV8UsPHE/dE8FhRlF01gYhk5SAumWu7ZCgWKueKoqdLY1DpPECxREJPJxA9P9MCZiCJUHGUieiWIdrb8byguXpRsvZdgZ96xHi+OkCFGMsQvc8MLzFzGyNdKwywUTfedpFfQ1i0yz9mc45TqTiuf+MMBqgSKnoPeiyXAgnhdEH4+eeT8awoM60u5Aw72/qY39KiCq1GdNuHx1fYH2DpazwDJeTyPWN3cyyL0CAHKdxQrYrEakX7WsqqHOlivGnplKjcHkUTYTB9BVHRZ+Wu5NAZwvYVIvQ/Dr7QJvvw3YufIv3bEOmi52CSFAZhhADnctN1q/ssuloKBZky0pWjiPC5Jykr57qz+yjW7j" />
</div>
	<script type="text/javascript" language="javascript" src="js/ToolTipPopUp.js"></script>
	<script type="text/javascript">
//<![CDATA[
Sys.WebForms.PageRequestManager._initialize('ScriptManager1', 'form1', ['tUpdatePanel2',''], ['btnSumit',''], [], 90, '');
//]]>
</script>

	
	<div id="Everything" class="">
		<div id="Search" class="SearchDIV">
            <div id="upProgPnl" style="display:none;">
	
			        <!--<DIV id="IMGDIV" align="center" valign="middle" style="position: absolute;left: 50%;top: 50%;visibility:visible;vertical-align:middle;background-color:White">-->
			        <img id="imgProgress" src="images/preloader_01.gif" style="border-width:0px;" />
			        <!--</DIV>-->
		        
</div>
			<table id="Table1" border="0" cellpadding="0" width="100%">
	<tr>
		<td class="SearchHeader">
						<center>
							Search Inmates</center>
					</td>
	</tr>
	<tr>
		<td>
						Last Name:
					</td>
	</tr>
	<tr>
		<td>
						<input name="txbLastName" type="text" id="txbLastName" />
					</td>
	</tr>
	<tr>
		<td>
						First Name:
					</td>
	</tr>
	<tr>
		<td>
						<input name="txbFirstName" type="text" id="txbFirstName" />
					</td>
	</tr>
	<tr>
		<td>
						Middle Name:
					</td>
	</tr>
	<tr>
		<td>
						<input name="txbMiddleName" type="text" id="txbMiddleName" />
					</td>
	</tr>
	<tr>
		<td>
						Begin Booking Date:
					</td>
	</tr>
	<tr>
		<td>
						<input name="tbBeginDate" type="text" id="tbBeginDate" />
						
					</td>
	</tr>
	<tr>
		<td>
						End Booking Date:
					</td>
	</tr>
	<tr>
		<td>
						<input name="tbEndDate" type="text" id="tbEndDate" />
						
					</td>
	</tr>
	<tr>
		<td id="BeginReleaseDateLabel" style="display: none;">
						Begin Release Date:
					</td>
	</tr>
	<tr>
		<td>
						<input name="tbBeginReleaseDate" type="text" id="tbBeginReleaseDate" style="display: none;" />
						
					</td>
	</tr>
	<tr>
		<td id="EndReleaseDateLabel" style="display: none;">
						End Release Date:
					</td>
	</tr>
	<tr>
		<td>
						<input name="tbEndReleaseDate" type="text" id="tbEndReleaseDate" style="display: none;" />
						
					</td>
	</tr>
	<tr>
		<td>
						Search For:
					</td>
	</tr>
	<tr>
		<td>
						<select name="TypeSearch" id="TypeSearch" onChange="SearchTypeSelect();">
			<option value="0">Current Inmates Only</option>
			<option value="1">Released Inmates Only</option>
			<option value="2">Both Current And Released</option>

		</select>
					</td>
	</tr>
	<tr>
		<td>
						<table>
							<tr>
								<td style="width: 80px">
									Sorted By:
								</td>
								<td>
									<select name="SearchSortOption" id="SearchSortOption">
			<option value="0">Name</option>
			<option value="1">Booking Date</option>

		</select>
								</td>
							</tr>
							<tr>
								<td>
									Order:
								</td>
								<td>
									<select name="SearchOrderOption" id="SearchOrderOption">
			<option value="0">Ascending</option>
			<option value="1">Descending</option>

		</select>
								</td>
							</tr>
						</table>
					</td>
	</tr>
	<tr>
		<td>
						<input type="submit" name="btnSumit" value="Submit" onclick="javascript:WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions(&quot;btnSumit&quot;, &quot;&quot;, true, &quot;&quot;, &quot;&quot;, false, false))" id="btnSumit" /><input type="submit" name="btnReset" value="Reset" id="btnReset" />
					</td>
	</tr>
	<tr>
		<td>
						&nbsp;
					</td>
	</tr>
	<tr>
		<td>
						&nbsp;
					</td>
	</tr>
	<tr>
		<td>
					     
					</td>
	</tr>
</table>

		</div>
        

		
        

		<div id="grid" class="GridDIV">
			<span id="UpdatePanel2">
					<span id="ControlInput" style="color:Red;display:none;">Please fill in at least one search criteria.</span>
					<center>
						<span id="ResultsReturned" Value="0" style="display:none">4</span>
						<span id="lbGridInfo" class="DivCountMsg">BOOKED Last 24 Hours</span></center>
					</BR>
					<br />
                    <table >
                        <tr>
                            <td>
                                <div id="JailInfo" >
						        <table border="0" cellpadding="0" cellspacing="2" class="JailView">
							        
								        
									        <tr style="InmateRecordRow">
										        <td nowrap="nowrap" width="2%">
                                                    <img src='ViewImage.aspx?bookno=PCSO26JBN002606'><BR><a href="ViewImageFull.aspx?bookno=PCSO26JBN002606" target='blank'>Enlarge Photo</a>
	                                                
										        </td>
										        <td nowrap="nowrap" valign="top">
											        <table border="0" cellpadding="1" cellspacing="0" width="100%">
												        <thead>
													        <tr>
														        <td class="SearchHeader" colspan="4">
															        BISHOP, AMY LEIGH
															        &nbsp; (W/
															        FEMALE
															        
																	
															        )
														        </td>
													        </tr>
												        </thead>
												        <tbody>
													        <tr>
														        <td class="InmateInfoGridTd" style="">
															        Status:
														        </td>
														        <td class="InmateInfoGridTd">
															        In Jail
														        </td>
														        
														        
													        </tr>
													        <tr class="oddNoWidth">
														        <td class="InmateInfoGridTd">
															        Booking No:
														        </td>
														        <td class="InmateInfoGridTd">
															        PCSO26JBN002606
														        </td>
														        <td class="InmateInfoGridTd">
															        MniNo:
														        </td>
														        <td class="InmateInfoGridTd">
															        PCSO03MNI234856
														        </td>
													        </tr>
													        <tr>
														        <td class="InmateInfoGridTd">
															        Booking Date:
														        </td>
                                                                <td class="InmateInfoGridTd">09/16/2026 07:05 AM</td>
														        
													        </tr>
													        <tr class="oddNoWidth">
														        <td class="InmateInfoGridTd">
															        Age On Booking Date:
														        </td>
														        <td class="InmateInfoGridTd">
															        40
														        </td>
														        <td class="InmateInfoGridTd">
														        </td>
														        <td class="InmateInfoGridTd">
														        </td>
													        </tr>
													        <tr>
														        <td class="InmateInfoGridTd">
															        Bond Amount:
														        </td>
														        <td class="InmateInfoGridTd">
															        $0.00
														        </td>
																
																<td class="InmateInfoGridTd" colspan="2"></td>
																
													        </tr>
													        <tr class="oddNoWidth">
														        
														
													        </tr>
													        <tr class="oddNoWidth"><td class="InmateInfoGridTd" nowrap="nowrap" width="2%">Address Given:</td><td colspan="3" style="min-width: 500px;" class="InmateInfoGridTd">1008 MARION AVE INTERLACHEN, FL 32148</td></tr>
												        </tbody>
											        </table>
										        </td>
									        </tr>
											<tr class="InmateRecordSeperater" ></tr>
											
									        <tr class="InmateRecordSeperater" ></tr>
									        
											        <tr>
												        <td colspan="2" valign="top">
													        <table class="JailViewCharges" id="JailViewCharges" border="0" cellpadding="2" cellspacing="0"
														        width="100%">
														        <tr>
															        <td class="SearchHeader" colspan="6">
																        CHARGES
															        </td>
														        </tr>
														        <tr class="SearchHeader">
															        <td>
															        </td>
															        <td>
																        STATUTE
															        </td>
															        <td>
																        COURT CASE NUMBER
															        </td>
															        <td>
																        CHARGE
															        </td>
															        <td>
																        DEGREE
															        </td>
															        <td>
																        LEVEL
															        </td>
															        <td>
																        BOND
															        </td>
																	
														        </tr>
										        
											        <tr>
												        <td nowrap="nowrap" id="expander3dcb556022354a64a9fb66e87fc40c78" onclick="ToggleExpand(this.id)">[+]</td>
												        <td nowrap="nowrap">
													        812.014.2c3
												        </td>
												        <td nowrap="nowrap">
													        261056CF (PUTNAM COUNTY SHERIFF)
												        </td>
												        <td nowrap="nowrap">
													        LARC
												        </td>
												        <td nowrap="nowrap">
													        S
												        </td>
												        <td nowrap="nowrap">
													        F
												        </td>
												        <td nowrap="nowrap">
													        $15000.00</br>
												        </td>
														<tr><td nowrap="nowrap" colspan="8" id="expanded3dcb556022354a64a9fb66e87fc40c78"style="display:none;text-align:left">10K DOLS LESS 20K DOLS STATE OF EMERGENCY/RIOT</td></tr>
											        </tr>
										        
											        <tr class="odd">
												        <td nowrap="nowrap" id="expander3959b758b9884d08a6def3e1e23d0f42" onclick="ToggleExpand(this.id)">[+]</td>
												        <td nowrap="nowrap">
													        812.019.1
												        </td>
												        <td nowrap="nowrap">
													        261056CF (PUTNAM COUNTY SHERIFF)
												        </td>
												        <td nowrap="nowrap">
													        STOLEN PROP-DEAL IN
												        </td>
												        <td nowrap="nowrap">
													        S
												        </td>
												        <td nowrap="nowrap">
													        F
												        </td>
												        <td nowrap="nowrap">
													        $15000.00
                                                            <br></br>
												        </td>
														
                                                        <tr><td class="odd" nowrap="nowrap" colspan="8" id="expanded3959b758b9884d08a6def3e1e23d0f42"style="display:none;text-align:left">DEALING TRAFFIC STOLEN PROPERTY</td></tr>
											        </tr>
										        
                                                    </table></BR></BR></BR></td></tr>
											    
								        
									        <tr style="InmateRecordRow">
										        <td nowrap="nowrap" width="2%">
                                                    <img src='ViewImage.aspx?bookno=PCSO26JBN002609'><BR><a href="ViewImageFull.aspx?bookno=PCSO26JBN002609" target='blank'>Enlarge Photo</a>
	                                                
										        </td>
										        <td nowrap="nowrap" valign="top">
											        <table border="0" cellpadding="1" cellspacing="0" width="100%">
												        <thead>
													        <tr>
														        <td class="SearchHeader" colspan="4">
															        DAVIS, DARI'ELLE TA'TIONNA ZMARE
															        &nbsp; (B/
															        FEMALE
															        
																	
															        )
														        </td>
													        </tr>
												        </thead>
												        <tbody>
													        <tr>
														        <td class="InmateInfoGridTd" style="">
															        Status:
														        </td>
														        <td class="InmateInfoGridTd">
															        In Jail
														        </td>
														        
														        
													        </tr>
													        <tr class="oddNoWidth">
														        <td class="InmateInfoGridTd">
															        Booking No:
														        </td>
														        <td class="InmateInfoGridTd">
															        PCSO26JBN002609
														        </td>
														        <td class="InmateInfoGridTd">
															        MniNo:
														        </td>
														        <td class="InmateInfoGridTd">
															        PCSO18MNI001589
														        </td>
													        </tr>
													        <tr>
														        <td class="InmateInfoGridTd">
															        Booking Date:
														        </td>
                                                                <td class="InmateInfoGridTd">09/16/2026 08:13 PM</td>
														        
													        </tr>
													        <tr class="oddNoWidth">
														        <td class="InmateInfoGridTd">
															        Age On Booking Date:
														        </td>
														        <td class="InmateInfoGridTd">
															        28
														        </td>
														        <td class="InmateInfoGridTd">
														        </td>
														        <td class="InmateInfoGridTd">
														        </td>
													        </tr>
													        <tr>
														        <td class="InmateInfoGridTd">
															        Bond Amount:
														        </td>
														        <td class="InmateInfoGridTd">
															        NO BOND
														        </td>
																
																<td class="InmateInfoGridTd" colspan="2"></td>
																
													        </tr>
													        <tr class="oddNoWidth">
														        
														
													        </tr>
													        <tr class="oddNoWidth"><td class="InmateInfoGridTd" nowrap="nowrap" width="2%">Address Given:</td><td colspan="3" style="min-width: 500px;" class="InmateInfoGridTd">1886 WATERWAY CR Apt 305 MIDDLEBERG, FL 32068</td></tr>
												        </tbody>
											        </table>
										        </td>
									        </tr>
											<tr class="InmateRecordSeperater" ></tr>
											
									        <tr class="InmateRecordSeperater" ></tr>
									        
											        <tr>
												        <td colspan="2" valign="top">
													        <table class="JailViewCharges" id="JailViewCharges" border="0" cellpadding="2" cellspacing="0"
														        width="100%">
														        <tr>
															        <td class="SearchHeader" colspan="6">
																        CHARGES
															        </td>
														        </tr>
														        <tr class="SearchHeader">
															        <td>
															        </td>
															        <td>
																        STATUTE
															        </td>
															        <td>
																        COURT CASE NUMBER
															        </td>
															        <td>
																        CHARGE
															        </td>
															        <td>
																        DEGREE
															        </td>
															        <td>
																        LEVEL
															        </td>
															        <td>
																        BOND
															        </td>
																	
														        </tr>
										        
											        <tr>
												        <td nowrap="nowrap" id="expander209efd83f604415397a18da8b6937eae" onclick="ToggleExpand(this.id)">[+]</td>
												        <td nowrap="nowrap">
													        784.03.1a2
												        </td>
												        <td nowrap="nowrap">
													        0 (PALATKA POLICE DEPARTMENT)
												        </td>
												        <td nowrap="nowrap">
													        BATTERY
												        </td>
												        <td nowrap="nowrap">
													        F
												        </td>
												        <td nowrap="nowrap">
													        M
												        </td>
												        <td nowrap="nowrap">
													        NO BOND</br>
												        </td>
														<tr><td nowrap="nowrap" colspan="8" id="expanded209efd83f604415397a18da8b6937eae"style="display:none;text-align:left">CAUSE BODILY HARM</td></tr>
											        </tr>
										        
                                                    </table></BR></BR></BR></td></tr>
											    
								        
									        <tr style="InmateRecordRow">
										        <td nowrap="nowrap" width="2%">
                                                    <img src='ViewImage.aspx?bookno=PCSO26JBN002610'><BR><a href="ViewImageFull.aspx?bookno=PCSO26JBN002610" target='blank'>Enlarge Photo</a>
	                                                
										        </td>
										        <td nowrap="nowrap" valign="top">
											        <table border="0" cellpadding="1" cellspacing="0" width="100%">
												        <thead>
													        <tr>
														        <td class="SearchHeader" colspan="4">
															        LEWIS, FREDDIE CLARENCE
															        &nbsp; (B/
															        MALE
															        
																	
															        )
														        </td>
													        </tr>
												        </thead>
												        <tbody>
													        <tr>
														        <td class="InmateInfoGridTd" style="">
															        Status:
														        </td>
														        <td class="InmateInfoGridTd">
															        In Jail
														        </td>
														        
														        
													        </tr>
													        <tr class="oddNoWidth">
														        <td class="InmateInfoGridTd">
															        Booking No:
														        </td>
														        <td class="InmateInfoGridTd">
															        PCSO26JBN002610
														        </td>
														        <td class="InmateInfoGridTd">
															        MniNo:
														        </td>
														        <td class="InmateInfoGridTd">
															        PCSO11MNI002943
														        </td>
													        </tr>
													        <tr>
														        <td class="InmateInfoGridTd">
															        Booking Date:
														        </td>
                                                                <td class="InmateInfoGridTd">09/16/2026 11:13 PM</td>
														        
													        </tr>
													        <tr class="oddNoWidth">
														        <td class="InmateInfoGridTd">
															        Age On Booking Date:
														        </td>
														        <td class="InmateInfoGridTd">
															        40
														        </td>
														        <td class="InmateInfoGridTd">
														        </td>
														        <td class="InmateInfoGridTd">
														        </td>
													        </tr>
													        <tr>
														        <td class="InmateInfoGridTd">
															        Bond Amount:
														        </td>
														        <td class="InmateInfoGridTd">
															        $0.00
														        </td>
																
																<td class="InmateInfoGridTd" colspan="2"></td>
																
													        </tr>
													        <tr class="oddNoWidth">
														        
														
													        </tr>
													        <tr class="oddNoWidth"><td class="InmateInfoGridTd" nowrap="nowrap" width="2%">Address Given:</td><td colspan="3" style="min-width: 500px;" class="InmateInfoGridTd">116 E OAK HILL DR PALATKA, FL 32177</td></tr>
												        </tbody>
											        </table>
										        </td>
									        </tr>
											<tr class="InmateRecordSeperater" ></tr>
											
									        <tr class="InmateRecordSeperater" ></tr>
									        
											        <tr>
												        <td colspan="2" valign="top">
													        <table class="JailViewCharges" id="JailViewCharges" border="0" cellpadding="2" cellspacing="0"
														        width="100%">
														        <tr>
															        <td class="SearchHeader" colspan="6">
																        CHARGES
															        </td>
														        </tr>
														        <tr class="SearchHeader">
															        <td>
															        </td>
															        <td>
																        STATUTE
															        </td>
															        <td>
																        COURT CASE NUMBER
															        </td>
															        <td>
																        CHARGE
															        </td>
															        <td>
																        DEGREE
															        </td>
															        <td>
																        LEVEL
															        </td>
															        <td>
																        BOND
															        </td>
																	
														        </tr>
										        
											        <tr>
												        <td nowrap="nowrap" id="expanderf9b5eaead50a45b5a8ed129cc7475e28" onclick="ToggleExpand(this.id)">[+]</td>
												        <td nowrap="nowrap">
													        843.02
												        </td>
												        <td nowrap="nowrap">
													        00 (PALATKA POLICE DEPARTMENT)
												        </td>
												        <td nowrap="nowrap">
													        RESIST OFFICER
												        </td>
												        <td nowrap="nowrap">
													        F
												        </td>
												        <td nowrap="nowrap">
													        M
												        </td>
												        <td nowrap="nowrap">
													        $500.00</br>
												        </td>
														<tr><td nowrap="nowrap" colspan="8" id="expandedf9b5eaead50a45b5a8ed129cc7475e28"style="display:none;text-align:left">OBSTRUCT WO VIOLENCE</td></tr>
											        </tr>
										        
											        <tr class="odd">
												        <td nowrap="nowrap" id="expandere1af30ee3819434ea6d020d72ced6b43" onclick="ToggleExpand(this.id)">[+]</td>
												        <td nowrap="nowrap">
													        900.04
												        </td>
												        <td nowrap="nowrap">
													        120576DR (PALATKA POLICE DEPARTMENT)
												        </td>
												        <td nowrap="nowrap">
													        CONTEMPT OF COURT
												        </td>
												        <td nowrap="nowrap">
													        N
												        </td>
												        <td nowrap="nowrap">
													        N
												        </td>
												        <td nowrap="nowrap">
													        $300.00
                                                            <br></br>
												        </td>
														
                                                        <tr><td class="odd" nowrap="nowrap" colspan="8" id="expandede1af30ee3819434ea6d020d72ced6b43"style="display:none;text-align:left">0</td></tr>
											        </tr>
										        
                                                    </table></BR></BR></BR></td></tr>
											    
								        
									        <tr style="InmateRecordRow">
										        <td nowrap="nowrap" width="2%">
                                                    <img src='ViewImage.aspx?bookno=PCSO26JBN002607'><BR><a href="ViewImageFull.aspx?bookno=PCSO26JBN002607" target='blank'>Enlarge Photo</a>
	                                                
										        </td>
										        <td nowrap="nowrap" valign="top">
											        <table border="0" cellpadding="1" cellspacing="0" width="100%">
												        <thead>
													        <tr>
														        <td class="SearchHeader" colspan="4">
															        PARSON, PATRICK LYNN
															        &nbsp; (W/
															        MALE
															        
																	
															        )
														        </td>
													        </tr>
												        </thead>
												        <tbody>
													        <tr>
														        <td class="InmateInfoGridTd" style="">
															        Status:
														        </td>
														        <td class="InmateInfoGridTd">
															        In Jail
														        </td>
														        
														        
													        </tr>
													        <tr class="oddNoWidth">
														        <td class="InmateInfoGridTd">
															        Booking No:
														        </td>
														        <td class="InmateInfoGridTd">
															        PCSO26JBN002607
														        </td>
														        <td class="InmateInfoGridTd">
															        MniNo:
														        </td>
														        <td class="InmateInfoGridTd">
															        PCSO26MNI005832
														        </td>
													        </tr>
													        <tr>
														        <td class="InmateInfoGridTd">
															        Booking Date:
														        </td>
                                                                <td class="InmateInfoGridTd">09/16/2026 11:54 AM</td>
														        
													        </tr>
													        <tr class="oddNoWidth">
														        <td class="InmateInfoGridTd">
															        Age On Booking Date:
														        </td>
														        <td class="InmateInfoGridTd">
															        43
														        </td>
														        <td class="InmateInfoGridTd">
														        </td>
														        <td class="InmateInfoGridTd">
														        </td>
													        </tr>
													        <tr>
														        <td class="InmateInfoGridTd">
															        Bond Amount:
														        </td>
														        <td class="InmateInfoGridTd">
															        $0.00
														        </td>
																
																<td class="InmateInfoGridTd" colspan="2"></td>
																
													        </tr>
													        <tr class="oddNoWidth">
														        
														
													        </tr>
													        <tr class="oddNoWidth"><td class="InmateInfoGridTd" nowrap="nowrap" width="2%">Address Given:</td><td colspan="3" style="min-width: 500px;" class="InmateInfoGridTd">329 S. US HIGHWAY 17 2 EAST PALATKA, FL 32131</td></tr>
												        </tbody>
											        </table>
										        </td>
									        </tr>
											<tr class="InmateRecordSeperater" ></tr>
											
									        <tr class="InmateRecordSeperater" ></tr>
									        
											        <tr>
												        <td colspan="2" valign="top">
													        <table class="JailViewCharges" id="JailViewCharges" border="0" cellpadding="2" cellspacing="0"
														        width="100%">
														        <tr>
															        <td class="SearchHeader" colspan="6">
																        CHARGES
															        </td>
														        </tr>
														        <tr class="SearchHeader">
															        <td>
															        </td>
															        <td>
																        STATUTE
															        </td>
															        <td>
																        COURT CASE NUMBER
															        </td>
															        <td>
																        CHARGE
															        </td>
															        <td>
																        DEGREE
															        </td>
															        <td>
																        LEVEL
															        </td>
															        <td>
																        BOND
															        </td>
																	
														        </tr>
										        
											        <tr>
												        <td nowrap="nowrap" id="expanderb25f771ba7ad4aa980a593e9f32296d3" onclick="ToggleExpand(this.id)">[+]</td>
												        <td nowrap="nowrap">
													        787.02.1a
												        </td>
												        <td nowrap="nowrap">
													        0 (PUTNAM COUNTY SHERIFF)
												        </td>
												        <td nowrap="nowrap">
													        KIDNAP-FALSE IMPRISONMENT
												        </td>
												        <td nowrap="nowrap">
													        T
												        </td>
												        <td nowrap="nowrap">
													        F
												        </td>
												        <td nowrap="nowrap">
													        $0.00</br>
												        </td>
														<tr><td nowrap="nowrap" colspan="8" id="expandedb25f771ba7ad4aa980a593e9f32296d3"style="display:none;text-align:left">ADULT</td></tr>
											        </tr>
										        
                                                    </table></BR></BR></BR></td></tr>
											    
								        
								        
						        </table>
		                        </div>
                            </td>
                        </tr>
                        <tr id="LoadMoreRow" class="LoadMoreRow">
                            <td style="height:35px;">
                                <div id="LoadMoreButton" class="LoadMoreButton" onclick="LoadMoreResults()" onmouseover="LoadMoreMouseEnter()" onmouseout="LoadMoreMouseLeave()">
                                     <p>Load more results<p>
                                </div>
                            </td>
                        </tr>
                        <tr id="PrintRow" class="noPrint">
                            <td style="width:100px;">
                                <center><a id="PrintLink" class="noPrint" href="javascript:PrintPreview();" >Print</a></center>
                            </td>
                        </tr>
                    </table>
                </span>
            </div>
        
        <div style="font-size: 6pt;float: right;position: fixed;bottom: 20px;">
            <div style="font-size: 8pt;">
	            Contact: &amp;amp;amp;amp;nbsp;
            </div>
            <a href="http://cts-america.com" title="http://cts-america.com" class="logo" target="_blank">
				<img id="CTSLogo" src="images/SmartCOP%20horizontal-01.png" style="border-width:0px;" />
			</a>
			<div style="font-size: 6pt;bottom: 0;">Version:3.0.1.11</div>
        </div>
		
		
		<div style="margin-top: 10px;margin-right: 0px; position: fixed; right: 10px;" class="noPrint">
			
		</div>
		
        
        </div>
            
					
	
<script type="text/javascript">
//<![CDATA[
var Page_Validators =  new Array(document.getElementById("ControlInput"));
//]]>
</script>

<script type="text/javascript">
//<![CDATA[
var ControlInput = document.all ? document.all["ControlInput"] : document.getElementById("ControlInput");
ControlInput.errormessage = "Please Fill In At Least One Search Criteria.";
ControlInput.display = "Dynamic";
ControlInput.evaluationfunction = "CustomValidatorEvaluateIsValid";
//]]>
</script>


<script type="text/javascript">
//<![CDATA[

var Page_ValidationActive = false;
if (typeof(ValidatorOnLoad) == "function") {
    ValidatorOnLoad();
}

function ValidatorOnSubmit() {
    if (Page_ValidationActive) {
        return ValidatorCommonOnSubmit();
    }
    else {
        return true;
    }
}
        Sys.Application.add_init(function() {
    $create(Sys.UI._UpdateProgress, {"associatedUpdatePanelId":null,"displayAfter":100,"dynamicLayout":true}, null, null, $get("upProgPnl"));
});
Sys.Application.add_init(function() {
    $create(Sys.Extended.UI.CalendarBehavior, {"id":"dtBeginDate"}, {"dateSelectionChanged":focus}, null, $get("tbBeginDate"));
});
Sys.Application.add_init(function() {
    $create(Sys.Extended.UI.CalendarBehavior, {"id":"dtEndDate"}, {"dateSelectionChanged":focus}, null, $get("tbEndDate"));
});
Sys.Application.add_init(function() {
    $create(Sys.Extended.UI.CalendarBehavior, {"id":"dtBeginReleaseDate"}, null, null, $get("tbBeginReleaseDate"));
});
Sys.Application.add_init(function() {
    $create(Sys.Extended.UI.CalendarBehavior, {"id":"dtEndReleaseDate"}, null, null, $get("tbEndReleaseDate"));
});
Sys.Application.add_init(function() {
    $create(Sys.Extended.UI.Animation.UpdatePanelAnimationBehavior, {"id":"upPE2","onUpdated":"{\"AnimationName\":\"Sequence\",\"AnimationChildren\":[{\"AnimationName\":\"Parallel\",\"duration\":\".20\",\"Fps\":\"30\",\"AnimationChildren\":[{\"AnimationName\":\"FadeIn\",\"minimumOpacity\":\"0.2\",\"TargetScript\":\"$get(\\u0027UpdatePanel2\\u0027)\",\"AnimationChildren\":[]}]}]}","onUpdating":"{\"AnimationName\":\"Sequence\",\"AnimationChildren\":[{\"AnimationName\":\"Parallel\",\"duration\":\".20\",\"Fps\":\"30\",\"AnimationChildren\":[{\"AnimationName\":\"FadeOut\",\"minimumOpacity\":\"0.2\",\"TargetScript\":\"$get(\\u0027UpdatePanel2\\u0027)\",\"AnimationChildren\":[]}]}]}","triggerControlsClientID":["btnSumit"],"updatePanelClientID":"UpdatePanel2","updatePanelID":"UpdatePanel2"}, null, null, $get("UpdatePanel2"));
});

document.getElementById('ControlInput').dispose = function() {
    Array.remove(Page_Validators, document.getElementById('ControlInput'));
}
//]]>
</script>
</form>
	<script type="text/javascript">

		function UpdateFinished(sender, args) {
			$.ajax({
				type: "POST",
				url: "Jail.aspx/getRecordsToLoad",
				data: JSON.stringify(SearchVals),
				contentType: "application/json; charset=utf-8",
				dataType: "json",
				success: function (msg) {
				    if ($("#ResultsReturned").html() < msg.d)
				    {
				        $("#LoadMoreRow").hide();
				    }
				    else {
				        $("#LoadMoreRow").show();

				    }
				    if ($("#ResultsReturned").html() > 0) {
				        if ($("#SiteCSS").val != "Print.css") {
				            $("#PrintRow").show();
				        }
				    }
				    else
				    {
				        $("#PrintRow").hide();
				    }
				}
			});
		}

		Sys.WebForms.PageRequestManager.getInstance().add_pageLoaded(UpdateFinished);

		var originalClick = $("[name='btnSumit']")[0].onclick;
		$("[name='btnSumit']")[0].onclick = null;

		$("[name='btnSumit']").click(function (eventData, eventObject) {
			SearchVals.LastName = $("#txbLastName").val();
			SearchVals.FirstName = $("#txbFirstName").val();
			SearchVals.MiddleName = $("#txbMiddleName").val();
			SearchVals.BeginBookDate = $("#tbBeginDate").val();
			SearchVals.EndBookDate = $("#tbEndDate").val();
			SearchVals.BeginReleaseDate = $("#tbBeginReleaseDate").val();
			SearchVals.EndReleaseDate = $("#tbEndReleaseDate").val();
			if ($("#TypeSearch").val() != null)
				SearchVals.TypeJailSearch = $("#TypeSearch").val();
			else 
				SearchVals.TypeJailSearch = 0;
			SearchVals.SortOption = $("#SearchSortOption").val();
			SearchVals.SortOrder = $("#SearchOrderOption").val();
			SearchVals.RecordsLoaded = 0;
		    SearchVals.IsDefault = false;
			originalClick(eventData, eventObject);
		});
	</script>
</body>
</html>
