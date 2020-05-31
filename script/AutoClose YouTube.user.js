// ==UserScript==
// @name         AutoClose YouTube
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Control the watch time and interval on YouTube
// @author       Oscar Cai
// @match        http://*.youtube.com/*
// @match        https://*.youtube.com/*
// @resource     ok_bg  https://github.com/blackmonkey/my_tools/blob/master/imgs/xiaobanlong_okay.png?raw=true
// @resource     nok_bg https://github.com/blackmonkey/my_tools/blob/master/imgs/xiaobanlong_warning.png?raw=true
// @grant        GM.setValue
// @grant        GM.getValue
// @grant        GM.getResourceUrl
// ==/UserScript==

const ONE_SECOND = 1000;
const TEN_SECONDS = 10 * ONE_SECOND;
const FIFTEEN_SECONDS = 15 * ONE_SECOND;
const THIRTY_SECONDS = 30 * ONE_SECOND;
const ONE_MINUTE = 60 * ONE_SECOND;
const HALF_HOUR = 30 * ONE_MINUTE;
const ONE_HOUR = 60 * ONE_MINUTE;
const ONE_HALF_HOURS = 90 * ONE_MINUTE;
const TWO_HOURS = 2 * ONE_HOUR;
const TWO_DAYS = 48 * ONE_HOUR;

const SATURDAY = 6;
const SUNDAY = 0;

const DEBUG = false;

function getMaxWatchDuration() {
    return DEBUG ? THIRTY_SECONDS : HALF_HOUR;
}

function getWatchInterval() {
    if (DEBUG) {
        return ONE_MINUTE;
    }

    var now = new Date();
    var day = now.getDay();
    if (day == SUNDAY || day == SATURDAY) {
        return TWO_DAYS; //ONE_HALF_HOURS;
    }
    return TWO_DAYS; //TWO_HOURS;
}

function getCheckWatchingInterval() {
    return ONE_SECOND;
}

function now() {
    return new Date().getTime();
}

function timeToHMS(ms) {
    var ts = new Date();
    ts.setTime(ms);
    var m = ts.getMinutes();
    var s = ts.getSeconds();
    return ts.getHours() + ":" + (m > 9 ? m : "0" + m) + ":" + (s > 9 ? s : "0" + s);
}

function durationToHMS(ms) {
    var hours = Math.floor(ms / 3600000);
    var minutes = Math.floor((ms - (hours * 3600000)) / 60000);
    var seconds = Math.floor((ms - (hours * 3600000) - (minutes * 60000)) / 1000);
    var info = '';
    if (hours > 0) {
        info += hours + "小时";
    }
    if (minutes > 0) {
        info += minutes + "分钟";
    }
    if (seconds > 0) {
        info += seconds + "秒";
    }
    return info;
}

function getLastWatchingStoppedAt() {
//    console.log("getLastWatchingStoppedAt()");
    return GM.getValue('lastWatchingStoppedAt', 0);
}

function setLastWatchingStoppedAt() {
//    console.log("setLastWatchingStoppedAt()");
    return GM.setValue('lastWatchingStoppedAt', now());
}

function getCurrentWatchingDuration() {
//    console.log("getCurrentWatchingDuration()");
    return GM.getValue('currentWatchingDuration', 0);
}

function setCurrentWatchingDuration(ms, callback) {
//    console.log("setCurrentWatchingDuration() ms=" + ms);
    return GM.setValue('currentWatchingDuration', ms).then(callback);
}

function createNotifyDiv() {
    var div = document.createElement("div");
    div.style.width = "100vw";
    div.style.height = "100vh";
    div.style.textAlign = "center";
    div.style.font = "bold 30pt tahoma,arial";
    div.style.backgroundRepeat = "no-repeat";
    div.style.backgroundSize = "100vw";
    div.style.margin = "0px 0px 0px 0px";
    div.style.paddingTop = "250pt";
    div.style.paddingLeft = "100pt";
    return div
}

function clearChildren(domObj) {
    domObj.textContent = "";
    domObj.innerHtml = "";
    domObj.innerText = "";
}

function notifyRest() {
    setCurrentWatchingDuration(0, setLastWatchingStoppedAt).then(getLastWatchingStoppedAt).then(function (lastWatchingStoppedAt) {
//        console.log("notifyRest()");
        var nextWatchingStart = lastWatchingStoppedAt + getWatchInterval();
        var restTime = nextWatchingStart - now();
        showNotifyMsg("果果，你已经看了很久的动画片了，现在需要休息眼睛了！", restTime, nextWatchingStart);
    });
}

var restTimeUpdatingTimer;

function notifyRestLonger(restTime, nextWatchingStart) {
    showNotifyMsg("果果，你眼睛休息的时间还不够哦！", restTime, nextWatchingStart);
}

function notifyCanWatch(divObj) {
    clearChildren(divObj);
    GM.getResourceUrl("ok_bg").then(function(link) {
        divObj.style.backgroundImage = "url(" + link + ")";
    });
    divObj.appendChild(document.createTextNode("不错哦，果果，你已经休息好了！"));
    divObj.appendChild(document.createElement("br"));

    var a = document.createElement("a");
    a.href = location.href;
    a.innerText = "现在可以继续看动画片了！";
    divObj.appendChild(a);
}

function showNotifyMsg(msg1, restTime, nextWatchingStart) {
    var br1 = document.createElement("br");
    var msg2 = document.createTextNode("要休息到 " + timeToHMS(nextWatchingStart) + "，还有");
    var restMsgSpan = document.createElement("span");
    restMsgSpan.innerText = durationToHMS(restTime);

    var div = createNotifyDiv();
    GM.getResourceUrl("nok_bg").then(function(link) {
        div.style.backgroundImage = "url(" + link + ")";
    });
    div.appendChild(document.createTextNode(msg1));
    div.appendChild(br1);
    div.appendChild(msg2);
    div.appendChild(restMsgSpan);
    div.appendChild(document.createTextNode("。"));

    clearChildren(document.body);
    document.body.appendChild(div);

    restTimeUpdatingTimer = setInterval(updateRestTime, 1000, div, restMsgSpan, nextWatchingStart);
}

function updateRestTime(divObj, spanObj, nextWatchingStart) {
    var restTime = nextWatchingStart - now();
    if (restTime > 1000) {
        spanObj.innerText = durationToHMS(restTime);
    } else {
        clearInterval(restTimeUpdatingTimer);
        notifyCanWatch(divObj);
    }
}

function checkRestAndWatching() {
    'use strict';
    getLastWatchingStoppedAt().then(function(lastWatchStoppedAt) {
        var maxWatchDuration = getMaxWatchDuration();
        var watchInterval = getWatchInterval();
        var nextWatchingStart = lastWatchStoppedAt + watchInterval;
        var restTime = nextWatchingStart - now();
        console.log("max watch duration: " + maxWatchDuration);
        console.log("watch interval: " + watchInterval);
        console.log("last watch stop: " + lastWatchStoppedAt + "=" + timeToHMS(lastWatchStoppedAt));
        console.log("next watch stop: " + (lastWatchStoppedAt + maxWatchDuration) + "=" + timeToHMS(lastWatchStoppedAt + maxWatchDuration));
        console.log("remain rest time: " + restTime + "=" + durationToHMS(restTime));
        console.log("next watch start: " + nextWatchingStart + "=" + timeToHMS(nextWatchingStart))
        if (restTime > 0) {
            notifyRestLonger(restTime, nextWatchingStart);
        } else {
            checkWatching();
        }
    })
}

function checkWatching() {
    getCurrentWatchingDuration().then(function(currentWatchingDuration) {
        console.log("current watching duration: " + currentWatchingDuration);
        if (currentWatchingDuration > getMaxWatchDuration()) {
            notifyRest();
        } else {
            var interval = getCheckWatchingInterval();
            setTimeout(setCurrentWatchingDuration, interval, currentWatchingDuration + interval, checkWatching);
        }
    });
}

checkRestAndWatching();