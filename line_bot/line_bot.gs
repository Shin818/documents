/**
 *百式用LINEbot 完成版
*/

var access_token = PropertiesService.getScriptProperties().getProperty("LINE_TOKEN");

var to = PropertiesService.getScriptProperties().getProperty("USER_ID");

function text_message(text){
    return {
        "type": "text",
        "text": text
    }
}

function choose_in_order(arrayData,isChange){
    //  var ss = SpreadsheetApp.getActiveSpreadsheet();
    //  var sheet = ss.getActiveSheet();

    var sheet = SpreadsheetApp.getActiveSheet();
    var arrayIndex = sheet.getRange(1,3,1,1).getValue();
    var index = arrayIndex+1;
    if(isChange == true){
        if(index < sheet.getLastRow()){
        sheet.getRange(1,3,1,1).setValue(arrayIndex+1);
        }else{
        sheet.getRange(1,3,1,1).setValue(1);
        }
    }
    return index-1+' : '+arrayData[arrayIndex-1][0]+' / '+arrayData[arrayIndex-1][1];
}


function getEngs() {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();
    var range = sheet.getRange(2,1,sheet.getLastRow()-1,2);
    var values = range.getValues();
    return values;
}

function messagePush(){
    var url = "https://api.line.me/v2/bot/message/multicast";
    var headers = {
        "Content-Type" : "application/json; charset=UTF-8",
        'Authorization': 'Bearer ' + access_token,
    };

    var word1 = choose_in_order(getEngs(),true);
    var word2 = choose_in_order(getEngs(),true);
    var word3 = choose_in_order(getEngs(),true);
    var word4 = choose_in_order(getEngs(),true);
    var word5 = choose_in_order(getEngs(),true);

    var postData = {
        "to" : [to],
        "messages" : [text_message(word1+'\n\n'+word2+'\n\n'+word3+'\n\n'+word4+'\n\n'+word5)]
    };

    var options = {
        "method" : "post",
        "headers" : headers,
        "payload" : JSON.stringify(postData)
    };

    return UrlFetchApp.fetch(url, options);
}
