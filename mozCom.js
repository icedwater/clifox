Cc = Components.classes;
Cr = Components.results;
Cu = Components.utils;
Ci = Components.interfaces;
XPCOMUtils = Cu.import("resource://gre/modules/XPCOMUtils.jsm").XPCOMUtils;
Array.prototype.indexOf = function(obj) {
    var idx = this.length;
    do {
        if (this[idx] == obj) {
            return idx;
        }
        idx--;
    } while (idx >= 0);
    return -1;
};

clifox.status = [];

clifox.runnable=function(cf,obj,func,args) {
this.id=clifox.justAddMap(this);
this.obj=obj;
this.func=func;
this.args=args;
this.clifox=cf;
this.ret=null;
};
clifox.runnable.prototype={
run:function(t) {
t.ret=t.func.apply(t.obj,t.args);
t.clifox.print({
"m":"e",
"t":"async",
"a":[t.id],
});
},
};

clifox.async=function() {
var v,obj,func,args,a;
a=arguments;
obj=a[0];
func=a[1];
args=[];
for(var i=2;i<a.length;i++) {
args.push(a[i]);
}
v=new clifox.runnable(clifox,obj,func,args);
clifox.getActiveTab().ownerDocument.defaultView.setTimeout(v.run,0,v);
};

clifox.onWindowCreate = function(w) {};
clifox.onWindowDestroy = function(w) {
if(w.mo) {
    w.mo.disconnect();
    w.mo = null;
}
};
//this is really the window for a document
//w.document might be available here?
clifox.onDocumentCreate = function(w) {
//clifox.note("onDocumentCreate",w);
try {
w.mo.disconnect();
w.mo.window=null;
w.mo=null;
} catch(e) {
};
    w.mo = new w.MutationObserver(clifox.notifyMutations);
w.mo.window=w
//clifox.note("w.mo",w.mo,"w.document",w.document);
    w.mo.observe(w.document, {
        "childList": 1,
        "attributes": 1,
        "characterData": 1,
        "subtree": 1
    });
};
clifox.notify = function(type,obj) {
var a;
clifox.print({
"m":"e",
"t":type?type:obj.type,
"a":[clifox.addMap(obj?obj:null)],
});
};
clifox.note = function() {
    var args, i;
    args = [];
    for (i = 0; i < arguments.length; i++) {
        args.push(arguments[i].toString());
    }
    clifox.print({
        "m": "e",
        "a": args
    });
};
clifox.addTab = function(url, tab) {
    var t;
    t = tab.parentNode.ownerDocument.defaultView.gBrowser.addTab();
    t.linkedBrowser.loadURI(url);
return t;
};
clifox.selectTab = function(t) {
//    clifox.note("selectTab.t", t.toString());
    t.parentNode.ownerDocument.defaultView.gBrowser.selectedTab = t;
    return t;
};
clifox.print = function(t) {
    if (!t['t']) {
        t['t'] = 'array'
    }
    clifox.handler.writeJ(t);
};
clifox.parentNodeNames = function(n) {
    var l, p;
    l = [];
    p = n.parentNode;
    while (p) {
        l.push(p.nodeName);
        p = p.parentNode;
    }
    return l;
};
clifox.getDomList = function(root, endings) {
    var n, l, i, num, nn, frames;
    num = 0;
    l = [];
    n = root;
    i = 0;
    frames = [];
    while (n && (i == 0 || n != root)) {
        if (num < 0 || (num == 0 && n != root)) {
            break;
        }
        i += 1;
        l.push([n, num]);
        nn = n.nodeName.toLowerCase();
        if (nn == "iframe" || nn == "frame") {
            frames.push(n.contentDocument);
            frames.push(n);
            n = n.contentDocument;
            num += 1;
            continue;
        }
        if (n.firstChild) {
            n = n.firstChild;
            num += 1;
            continue;
        }
        if (n.nextSibling) {
            n = n.nextSibling;
            continue;
        }
        while (n && !n.nextSibling) {
            if (n.nodeName == "#document" && frames.indexOf(n) > -1) {
                n = frames[frames.indexOf(n) + 1];
            } else {
                n = n.parentNode;
            }
            num -= 1;
            //if (endings && n){
            //l.push([0,n]);
            //}
        }
        if (!n) {
            break;
        }
        n = n.nextSibling;
    }
    return l;
};
clifox.time = function() {
    var d = new Date().getTime() / 1000;
    return d;
};
clifox.closeAll = function() {
    var i;
    for (i = this.gBrowser.tabs.length; i > 0; i--) {
        this.gBrowser.tabs[i].linkedBrowser.contentWindow.close();
    }
};
clifox.lsbrs = function() {
    var j, i, x;
    i = 0;
    j = [];
    for (i = 0; i < this.gBrowser.tabs.length; i++) {
        x = this.gBrowser.tabs[i].linkedBrowser.contentDocument.location.href;
        j.push(x);
    }
    return j.toString();
};
clifox.ls = function(obj) {
    var z;
    z = [];
    if (i) {
        var i;
        for (i in obj) {
            z.push(i);
        }
    }
    return z;
};
clifox.findAllInMap = function(parent) {
    var i, ret, oid, x;
    ret = [];
    for (i = clifox.map.length - 1; i >= 0; i--) {
        oid = clifox.map[i].id;
        x = clifox.map[i];
        while (x.parent) {
            if (x.id == parent) {
                ret.push(oid);
                break;
            }
            x = x.parent;
        }
    }
    return ret;
};
clifox.GuiListener = function() {
    var windows, i, wms,tabs;
    wms = clifox.getWms();
    wms.addListener(this);
    windows = clifox.listAllWindows();
    for (i = 0; i < windows.length; i++) {
        this.onOpenWindow(windows[i]);
    }
tabs=clifox.listAllTabs();
for(i=0;i<tabs.length;i++) {
clifox.onDocumentCreate(tabs[i].linkedBrowser.contentWindow);
}
};
clifox.GuiListener.prototype = {
    kill: function() {
        var windows, i, wms,tabs;
        wms = clifox.getWms();
        wms.removeListener(this);
        windows = clifox.listAllWindows();
        for (i = 0; i < windows.length; i++) {
            this.onCloseWindow(windows[i]);
        }
tabs=clifox.listAllTabs();
for(i=0;i<tabs.length;i++) {
clifox.onWindowDestroy(tabs[i].linkedBrowser.contentDocument.defaultView);
}
    },

    QueryInterface: XPCOMUtils.generateQI([Ci.nsIWebProgressListener, Ci.nsISupports, Ci.nsISupportsWeakReference]),

    onOpenWindow: function(w) {
        var win;
        win = w.QueryInterface(Ci.nsIInterfaceRequestor).getInterface(Ci.nsIDOMWindowInternal || Ci.nsIDOMWindow);
        win.gBrowser.addTabsProgressListener(this);
        //reenable this if onStateChange doesn't work
        //win.gBrowser.addEventListener("load",this.onDocumentLoad, false);
        win.gBrowser.addEventListener("pageshow", this.onDocumentPageshow, false);
        win.gBrowser.tabContainer.addEventListener("TabSelect", this, false);
        win.gBrowser.tabContainer.addEventListener("TabOpen", this, false);
        win.gBrowser.tabContainer.addEventListener("TabClose", this, false);
    },

    onCloseWindow: function(w) {
        var win;
        win = w.QueryInterface(Ci.nsIInterfaceRequestor).getInterface(Ci.nsIDOMWindowInternal || Ci.nsIDOMWindow);
        win.gBrowser.removeTabsProgressListener(this);
        win.gBrowser.removeEventListener("pageshow", this.onDocumentPageshow, false);
        win.gBrowser.tabContainer.removeEventListener("TabSelect", this, false);
        win.gBrowser.tabContainer.removeEventListener("TabOpen", this, false);
        win.gBrowser.tabContainer.removeEventListener("TabClose", this, false);
    },

    onDocumentLoad: function(ev) {
        try {
            if (ev.target.nodeName == "#document" && ev.target.location.href != "about:blank") {}
            clifox.print({
                "m": "e",
                "t": ev.type,
                "a": [clifox.addMap(ev)]
            });
        } catch (e) {
            clifox.onError(e);
        }
    },

    onDocumentPageshow: function(ev) {
        try {
            if (ev.target.nodeName == "#document" && ev.target.location.href != "about:blank") {}
            clifox.print({
                "m": "e",
                "t": ev.type,
                "a": [clifox.addMap(ev)]
            });
        } catch (e) {
            clifox.onError(e);
        }
    },

    handleEvent: function(aEvent) {
        return this.onEvent.apply(this, [aEvent]);
    },

    onEvent: function(ev) {
        try {
            clifox.print({
                "m": "e",
                "t": ev.type,
                "a": [clifox.addMap(ev)]
            });
        } catch (e) {
            clifox.onError(e);
        }
    },

    //readd if needed; for now, onStateChange tethered to a page_stop||is_window is doing the trick
    xx_onLocationChange: function(aWebProgress, aRequest, aURI) {
        try {
            var o = {
                "aWebProgress": aWebProgress,
                "aRequest": aRequest,
                "aURI": aURI
            };
            var oid = clifox.justAddMap(o);
            clifox.print({
                "m": "E",
                "a": [oid],
                "t": "onAddressChange"
            });
        } catch (e) {
            clifox.onError(e);
        }
    },

    onStatusChange: function(aBrowser, aWebProgress, aRequest, aStatus, aMessage) {
        var o, oid;
        if (clifox.status.indexOf(aMessage) > -1) {
            return;
        }
        try {
            o = {
                "aWebProgress": aWebProgress,
                "aRequest": aRequest,
                "aMessage": aMessage,
                "aStatus": aStatus
            };
            oid = clifox.justAddMap(o);
            clifox.print({
                "m": "E",
                "a": [oid],
                "t": "onStatusChange"
            });
            clifox.status.push(aMessage);
        } catch (e) {
            clifox.onError(e);
        }
    },

    onStateChange: function(aBrowser, aWebProgress, aRequest, aStateFlags, aStatus) {
        var o, oid, name;
//if there isn't a window, we don't want this to pass to python
//as we only care about page events we can actually see
if(!aWebProgress.DOMWindow) {
return;
}
        //clifox.print({"m":"w","a":["onStatusChange"]});
        if ((aStateFlags & Ci.nsIWebProgressListener.STATE_STOP) && (aStateFlags & Ci.nsIWebProgressListener.STATE_IS_WINDOW) && (aWebProgress.DOMWindow == aWebProgress.DOMWindow.top)) {
//specific to catch pages that are finished loading
//onStateChange triggers a page refresh
            name = "onStateChange";
        } else {
            name = "onStateChangeAll";
        }
        //clifox.print({"m":"w","a":["onStatusChange2"]});
        try {
            o = {
                "aWebProgress": aWebProgress,
                "aRequest": aRequest,
                "aStateFlags": aStateFlags,
                "aStatus": aStatus,
                "uri": aWebProgress.DOMWindow.location.href
            };
            oid = clifox.justAddMap(o);
            clifox.print({
                "m": "E",
                "a": [oid],
                "t": name,
            });
        } catch (e) {
            clifox.onError(e);
        }
    },

};

clifox.observer = function() {
    this.obs = Cc["@mozilla.org/observer-service;1"].getService(Ci.nsIObserverService);
    this.obs.addObserver(this, "content-document-global-created", false);
    this.obs.addObserver(this, "dom-window-destroyed", false);
};
clifox.observer.prototype = {
    kill: function() {
        this.obs.removeObserver(this, "content-document-global-created", false);
        this.obs.removeObserver(this, "dom-window-destroyed", false);
    },
    observe: function(aSubject, aTopic, aData) {
var o;
        clifox.print({
            "m": "w",
            "a": ["observer", aTopic]
        });
        if (aTopic == "content-document-global-created") {
//aSubject is indeed a window here
//aSubject.document should be available though, as that is why this event was fired
            o = aSubject.QueryInterface(Ci.nsIDOMWindow);
            clifox.onDocumentCreate(o);
        }
        if (aTopic == "dom-window-destroyed") {
            o = aSubject.QueryInterface(Ci.nsIDOMWindow);
            clifox.onWindowDestroy(o);
        }
    },
};

clifox.accView = function(aDocument) {
    function getAccessibleDoc(doc) {
        this.ar = Cc["@mozilla.org/accessibleRetrieval;1"].getService(Ci.nsIAccessibleRetrieval);
        this.ad = this.ar.getAccessibleFor(doc);
        return ad;
    };

    function getStates(aNode) {
        var d, e, ss, ret, i;
        d = {};
        e = {};
        ret = [];
        aNode.getState(d, e);
        ss = this.ar.getStringStates(d.value, e.value);
        for (i = 0; i < ss.length; i++) {
            ret.push(ss.item(i));
        }
        return ret;
    };

    function visit(aNode, l) {
var e;
        l.push(aNode);
        e = aNode.children.enumerate();
        while (e.hasMoreElements()) {
            visit(e.getNext(), l);
            l.push(-1);
        };
    };

    function getAccessibleTree(aNode, l) {
        var n, ns, i, root, num;
        num = 0;
        root = aNode;
        i = 0;
        n = aNode;
        while (n && (i == 0 || n != root)) {
            i += 1;
            l.push([n, num]);
            try {
                if (n.firstChild) {
                    n = n.firstChild;
                    num += 1;
                    continue;
                }
            } catch (e) {}
            try {
                if (n.nextSibling) {
                    n = n.nextSibling;
                    continue;
                }
            } catch (e) {}
            while (n != root) {
                try {
                    ns = n.nextSibling;
                } catch (e) {
                    ns = null;
                }
                if (ns) {
                    n = ns;
                    break;
                } else {
                    n = n.parent;
                    num -= 1;
                }
            }
            //n=n.nextSibling;
        }
        return l;
    };

    function serialize(aList, ret) {
        var i, n, role, states, text, num;
        for (i = 0; i < aList.length; i++) {
            n = aList[i];
            num = n[1];
            n = n[0];
            role = this.ar.getStringRole(n.role);
            states = getStates(n);
            if (role == "document" || role == "text leaf" || role == "statictext" || role == "text container" || !n.childCount) {
                text = n.name;
            } else {
                text = "";
            }
            ret.push([clifox.justAddMap(n), num, role, states, text]);
        }
    }
    var aDoc, l, ret;
    l = [];
    ret = [];
    aDoc = getAccessibleDoc(aDocument);
    //visit(aDoc,l);
    getAccessibleTree(aDoc, l);
    serialize(l, ret);
    return ret;
};

clifox.notifyMutations = function(records, observer) {
return;
    var r, t, i;
    //    if (gBrowser.selectedTab.linkedBrowser.contentWindow == observer.window) {
//clifox.note("observerInFunction",observer);
    if (observer.window.document.readyState == "complete") {
        //clifox.print({"m":"w","a":["notifyMutations",records.length]});
        r = [];
        t = [];
        for (i = 0; i < records.length; i++) {
            if (t.indexOf(records[i].target) < 0) {
                r.push(clifox.getDocJson(records[i].target));
                t.push(records[i].target);
            }
        }
        clifox.print({
            "m": "ec",
            "a": [r],
            "t": "mutation",
            "i": ""
        });
    }
};
clifox.getDocJson = function(root, func) {
    var atime, w, l, cur, ll, ww, skip, curElem, curWin, curGcs, nn, i, t, x, ids, grabVars;
    grabVars = {
        "A": ["textContent", "href", "title", "name"],
        "INPUT": ["title", "type", "value", "checked", "name", "disabled", "alt", "src"],
        "BUTTON": ["title", "type", "value", "checked", "name", "textContent", "disabled"],
        "TEXTAREA": ["name", "innerHTML", "disabled"],
        "SELECT": ["textContent", "value", "type", "selectedIndex", "disabled", "name"],
        "IMG": ["alt", "src", "title"],
        "LABEL": ["control"]
    };

    function getNode(x, func, ids) {
        var a, at, al, j, i, n, num, gv, gvl;
        num = x[1];
        n = x[0];
        a = [];
        a.push(func.apply(clifox, [n]));
        a.push(num);
        a.push(n.nodeName);
        a.push(n.nodeValue);
        //comment this out?
        a.push(0);
        //keep hashtable of ids for each run, and use the next lowest id to that of this element?
        a.push(num == 0 ? null : ids[num - 1]);
        //a.push(clifox.inMap(n.parentNode));
        //maybe just do grabvars[n.nodeName]?
        //if(grabVars.indexOf(n.nodeName)>-1)
        //{
        gv = grabVars[n.nodeName];
        if (gv) {
            gvl = gv.length;
            for (i = 0; i < gvl; i++) {
                a.push(gv[i]);
                a.push(n[gv[i]]);
            }
        }
        return a;
    }

    ids = {};
    if (!func) {
        if (clifox.inMap(root.firstChild) != null && clifox.inMap(root.lastChild) != null) {
            func = clifox.addMap;
        } else {
            func = clifox.justAddMap;
        }
    }
    //comment this out?
    //func=clifox.justAddMap;
    l = [];
    atime = clifox.time();
    w = this.getDomList(root);
    ll = w.length;
    ww = [];
    skip = -1;
    for (i = 0; i < ll; i++) {
        if (skip != -1 && w[i][1] > skip) {
            continue;
        }
        if (skip != -1) {
            skip = -1;
        }
        curElem = w[i][0];
        curWin = curElem.defaultView ? curElem.defaultView : curElem.ownerDocument.defaultView;
        //if(tt.offsetWidth==0&&tt.offsetHeight==0)
        //{
        try {
            curGcs = curWin.getComputedStyle(curElem);
        } catch (e) {
            curGcs = null;
        }
        //curGcs=null;
        //var elems=["LI","UL"];
        nn = curElem.nodeName.toLowerCase();
        //if(nn!="iframe"&&nn!="frame"&&nn!="#document")
        //{
        if (curGcs && (curGcs.visibility == 'hidden' || curGcs.display == 'none')) {
            skip = w[i][1];
            continue;
        }
        //}
        //}
        ww.push(w[i]);
    }
    ll = ww.length;
    for (i = 0; i < ll; i++) {
        t = ww[i];
        x = getNode(t, func, ids);
        l.push(x);
        ids[x[1]] = x[0];
    }
    //l.push(clifox.time()-atime);
    clifox.print({
        "m": "w",
        "a": ["docSerializationTime", clifox.time() - atime]
    });
    return l;
};
clifox.oldInit = function() {
    //clifox._unloadHandler=function(e){if(e.target.nodeName=="#document"){e.target.defaultView.removeEventListener("load",this._loadHandler,true);};};
    //clifox._loadHandler({});
    gBrowser.addEventListener("load", clifox._loadHandler, true);
    clifox.events.push([gBrowser, "load", clifox._loadHandler, true]);
    //gBrowser.addEventListener("unload", clifox._unloadHandler, true);
    ///
    clifox.web_progress_listener.init();
    clifox.killers.push([clifox.web_progress_listener, clifox.web_progress_listener.uninit]);
    ///
    var obs;
    clifox.windowGuiKiller.obs = obs;
    obs.addObserver(clifox.windowGuiKiller, "content-document-global-created", false);
    obs.addObserver(clifox.windowGuiKiller, "dom-window-destroyed", false);
    //content-document-global-created", false);
    clifox.killers.push([clifox.windowGuiKiller, clifox.windowGuiKiller.kill]);
    clifox.mutationObsObj.init();
    clifox.killers.push([clifox.mutationObsObj, clifox.mutationObsObj.kill]);
};
clifox.getActiveTab = function() {
    //uses focus manager to get window in focus (foreground)
    //gets selectedTab from that window
    var fm;
try {
    return clifox.fm.activeWindow.gBrowser.selectedTab;
} catch(e) {
return clifox.fm.activeWindow;
}
};
clifox.getWms = function() {
    if (this.wms) {
        return this.wms;
    }
    clifox.wms = Cc["@mozilla.org/appshell/window-mediator;1"].getService(Ci.nsIWindowMediator);
    return clifox.wms;
};
clifox.listAllWindows = function(t) {
    var wms, windows;
    windows = [];
    wms = clifox.getWms();
//    if(t==null) {
//t="navigator:browser"
//}
    windowsEnum = wms.getEnumerator(t);
    while (windowsEnum.hasMoreElements()) {
        windows.push(windowsEnum.getNext());
    }
    return windows;
};
clifox.listAllTabs = function() {
    var windows, tabs, w, i;
    tabs = [];
    windows = this.listAllWindows();
    for (i = 0; i < windows.length; i++) {
        w = windows[i];
        wTabs = w.getBrowser().tabContainer.childNodes;
        for (i = 0; i < wTabs.length; i++) {
            tabs.push(wTabs[i]);
        }
    }
    return tabs;
};
clifox.kill = function() {
    clifox.obs.kill();
    delete clifox.obs;
    clifox.gl.kill();
    delete clifox.gl;
};
clifox.init = function() {
    clifox.obs = new clifox.observer();
    clifox.gl = new clifox.GuiListener();
    if (!clifox.fm) {
        clifox.fm = Cc["@mozilla.org/focus-manager;1"].getService(Ci.nsIFocusManager);
    }
};
clifox.init();
