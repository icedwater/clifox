Array.prototype.indexOf = (function(obj) {
    var idx = this.length;
    do {
        if (this[idx] == obj) {
            return idx;
        };
        idx--;
    } while (idx >= 0);
    return -1;
});
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
        if (num < 0 || num == 0 && n != root) {
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
    for (var i = this.gBrowser.tabs.length; i > 0; i--) {
        this.gBrowser.tabs[i].linkedBrowser.contentWindow.close();
    };
};
clifox.lsbrs = function() {
    var j, i, x;
    i = 0;
    j = [];
    for (i = 0; i < this.gBrowser.tabs.length; i++) {
        x = this.gBrowser.tabs[i].linkedBrowser.contentDocument.location.href;
        j.push(x);
    };
    return j.toString();
};
clifox.ls = function(obj) {
    var z, i;
    z = [];
    for (i in obj) {
        z.push(i);
    };
    return z;
};
clifox.genid = function() {
    this._id += 1;
    return "j" + this._id.toString();
};
clifox.findAllInMap = function(parent) {
    var i, ret;
    ret = [];
    for (i = clifox.map.length - 1; i >= 0; i--) {
        var oid, x;
        oid = clifox.map[i].id;
        x = clifox.map[i];
        while (x.parent) {
            if (x.id == parent) {
                ret.push(oid);
                break;
            }
        }
    }
    return ret;
};
clifox.inMap = function(obj) {
    var where, i;
    where = obj['$clifox'];
    //clifox.print({"m":"w","a":["inMap",obj.toString()]});
    if (where) {
        return where;
    }
    where = clifox.mapObjList.indexOf(obj);
    if (where > -1) {
        return clifox.mapIdList[where];
    }
    return null;
};
clifox.addMap = function(obj, opts) {
    //clifox.print({"m":"w","a":clifox.inMap.toString()});
    var x;
    x = clifox.inMap(obj);
    if (x != null) {
        return x;
    };
    return clifox.justAddMap(obj, opts);
};
clifox.justAddMap = function(obj, opts) {
    var d, i, parent, name;
    i = clifox.genid();
    opts = opts ? opts : {};
    parent = opts.parent ? opts.parent : null;
    name = opts.name ? opts.name : "";
    d = {
        "parent": parent,
        "id": i,
        "value": obj,
        "type": typeof(obj),
        "name": name
    };
    clifox.map[i] = d;
    //clifox.map[i]=d;
    flag = 0;
    try {
        obj['$clifox'] = i;
        if (!obj['$clifox']) {
            flag = 1;
        }
    } catch (e) {
        flag = 1;
    }
    if (flag == 1) {
        clifox.mapIdList.push(i);
        clifox.mapObjList.push(obj);
    }
    //clifox.mapIdList.push(i);
    //clifox.mapObjList.push(obj);
    return i;
};
clifox._loadHandler = function(e) {
    try {
        if (e.target.nodeName == "#document" && e.target.location.href != "about:blank") {};
        clifox.print({
            "m": "e",
            "t": e.type,
            "a": [clifox.addMap(e)]
        });
    } catch (e) {
        clifox.print({
            "m": "w",
            "a": ["error:" + e.toString()]
        });
    };
};
//clifox._unloadHandler=function(e){if(e.target.nodeName=="#document"){e.target.defaultView.removeEventListener("load",this._loadHandler,true);};};
//clifox._loadHandler({});
gBrowser.addEventListener("load", clifox._loadHandler, true);
clifox.events.push([gBrowser, "load", clifox._loadHandler, true]);
//gBrowser.addEventListener("unload", clifox._unloadHandler, true);
clifox.web_progress_listener = {
    init: function() {
        //clifox.print({"m":"w","a":["R.WPL init"]});
        gBrowser.browsers.forEach(function(browser) {
            this._toggleProgressListener(browser.webProgress, true);
        }, this);
        gBrowser.tabContainer.addEventListener("TabSelect", this, false);
        gBrowser.tabContainer.addEventListener("TabOpen", this, false);
        gBrowser.tabContainer.addEventListener("TabClose", this, false);
    },

    uninit: function() {
        gBrowser.browsers.forEach(function(browser) {
            this._toggleProgressListener(browser.webProgress, false);
        }, this);
        gBrowser.tabContainer.removeEventListener("TabSelect", this, false);
        gBrowser.tabContainer.removeEventListener("TabOpen", this, false);
        gBrowser.tabContainer.removeEventListener("TabClose", this, false);
    },

    handleEvent: function(aEvent) {
        if (aEvent.type == "TabSelect") {
            try {
                var e = aEvent;
                clifox.print({
                    "m": "e",
                    "t": e.type,
                    "a": [clifox.addMap(e)]
                });
            } catch (e) {
                clifox.print({
                    "m": "t",
                    "a": [e.toString()]
                });
            };
        } else {
            let tab = aEvent.target;
            let webProgress = gBrowser.getBrowserForTab(tab).webProgress;
            this._toggleProgressListener(webProgress, ("TabOpen" == aEvent.type));
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
            clifox.print({
                "m": "t",
                "a": [e.toString()]
            });
        };
    },

    onStatusChange: function(aWebProgress, aRequest, aStatus, aMessage) {
        if (clifox.status.indexOf(aMessage) > -1) {
            return;
        }
        try {
            var o = {
                "aWebProgress": aWebProgress,
                "aRequest": aRequest,
                "aMessage": aMessage,
                "aStatus": aStatus
            };
            var oid = clifox.justAddMap(o);
            clifox.print({
                "m": "E",
                "a": [oid],
                "t": "onStatusChange"
            });
            clifox.status.push(aMessage);
        } catch (e) {
            clifox.print({
                "m": "t",
                "a": [e.toString()]
            });
        };
    },

    onStateChange: function(aWebProgress, aRequest, aStateFlags, aStatus) {
        //clifox.print({"m":"w","a":["onStatusChange"]});
        if ((aStateFlags & Components.interfaces.nsIWebProgressListener.STATE_STOP) && (aStateFlags & Components.interfaces.nsIWebProgressListener.STATE_IS_WINDOW) && (aWebProgress.DOMWindow == aWebProgress.DOMWindow.top)) {
            //clifox.print({"m":"w","a":["onStatusChange2"]});
            try {
                var o = {
                    "aWebProgress": aWebProgress,
                    "aRequest": aRequest,
                    "aStateFlags": aStateFlags,
                    "aStatus": aStatus,
                    "uri": aWebProgress.DOMWindow.location.href
                };
                var oid = clifox.justAddMap(o);
                clifox.print({
                    "m": "E",
                    "a": [oid],
                    "t": "onStateChange"
                });
            } catch (e) {
                clifox.print({
                    "m": "t",
                    "a": [e.toString()]
                });
            };
        } else {
            try {
                var o = {
                    "aWebProgress": aWebProgress,
                    "aRequest": aRequest,
                    "aStateFlags": aStateFlags,
                    "aStatus": aStatus,
                    "uri": aWebProgress.DOMWindow.location.href
                };
                var oid = clifox.justAddMap(o);
                clifox.print({
                    "m": "E",
                    "a": [oid],
                    "t": "onStateChangeAll"
                });
            } catch (e) {
                clifox.print({
                    "m": "t",
                    "a": [e.toString()]
                });
            };
        }
    },

    QueryInterface: function(aIID) {
        if (aIID.equals(Components.interfaces.nsIAuthPrompt2) || aIID.equals(Components.interfaces.nsIAuthPrompt) || aIID.equals(Components.interfaces.nsIWebProgressListener) || aIID.equals(Components.interfaces.nsISupportsWeakReference) || aIID.equals(Components.interfaces.nsISupports)) {
            return this;
        };
        throw Components.results.NS_NOINTERFACE;
    },

    prompt: function(dialogTitle, text, passwordRealm, savePassword, defaultText, result) {
        clifox.print({
            "M": "w",
            "a": ["authPrompt", dialogTitle, text, passwordRealm, savePassword, defaultText, result]
        });
        return true;
    },
    promptPassword: function(dialogTitle, text, passwordRealm, savePassword, pwd) {
        clifox.print({
            "M": "w",
            "a": ["authPromptPassword", dialogTitle, text, passwordRealm, savePassword, pwd]
        });
        return true;
    },
    promptUsernameAndPassword: function(dialogTitle, text, passwordRealm, savePassword, user, pwd) {
        clifox.print({
            "M": "w",
            "a": ["authPromptUsernameAndPassword", dialogTitle, text, passwordRealm, savePassword, user, pwd]
        });
        return true;
    },

    _toggleProgressListener: function(aWebProgress, aIsAdd) {
        if (aIsAdd) {
            aWebProgress.addProgressListener(this, aWebProgress.NOTIFY_ALL);
        } else {
            aWebProgress.removeProgressListener(this);
        }
    },
};
clifox.web_progress_listener.init();
clifox.killers.push([clifox.web_progress_listener, clifox.web_progress_listener.uninit]);

clifox.windowGuiKiller = {
    obs: null,
    observe: function(aSubject, aTopic, aData) {
        clifox.print({
            "m": "w",
            "a": ["observer", aTopic]
        });
        if (aTopic == "content-document-global-created") {
            var wo;
            aSubject.QueryInterface(Ci.nsIDOMWindow);
            if (aSubject.top == aSubject) {
                try {
                    clifox.mutationObsObj.add(aSubject);
                } catch (e) {
                    //clifox.print({"m":"w","a":[e.toString()]});
                }
            }
            wo = aSubject.wrappedJSObject;
            wo.alert = function() {};
            wo.confirm = function() {};
            wo.prompt = function() {};
        }
        if (aTopic == "dom-window-destroyed")
        //"content-document-global-created")
        {
            //this.kill();
            aSubject.QueryInterface(Ci.nsIDOMWindow);
            if (aSubject.mo) {
                aSubject.mo.disconnect();
                aSubject.mo = null;
            }
            wo = aSubject.wrappedJSObject;
            delete wo.alert;
            delete wo.confirm;
            delete wo.prompt;
        }
    },
    kill: function() {
        this.obs.removeObserver(this, "content-document-global-created");
        this.obs.removeObserver(this, "dom-window-destroyed");
    }
};

var obs;
obs = Components.classes["@mozilla.org/observer-service;1"].getService(Components.interfaces.nsIObserverService);
clifox.windowGuiKiller.obs = obs;
obs.addObserver(clifox.windowGuiKiller, "content-document-global-created", false);
obs.addObserver(clifox.windowGuiKiller, "dom-window-destroyed", false);
//content-document-global-created", false);
clifox.killers.push([clifox.windowGuiKiller, clifox.windowGuiKiller.kill]);

clifox.status = [];
clifox.accView = function(aDocument) {
    function getAccessibleDoc(doc) {
        this.ar = Components.classes["@mozilla.org/accessibleRetrieval;1"].getService(Components.interfaces.nsIAccessibleRetrieval);
        this.ad = this.ar.getAccessibleFor(doc);
        return ad;
    }

    function getStates(aNode) {
        var d, e, ss, ret;
        d = {};
        e = {};
        ret = [];
        aNode.getState(d, e);
        ss = this.ar.getStringStates(d.value, e.value);
        for (var i = 0; i < ss.length; i++) {
            ret.push(ss.item(i));
        }
        return ret;
    }

    function visit(aNode, l) {
        l.push(aNode);
        var e = aNode.children.enumerate();
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
    }

    function serialize(aList, ret) {
        var i;
        for (i = 0; i < aList.length; i++) {
            var n, role, states, text, num;
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
}
clifox.notifyMutations = function(records, observer) {
    if (gBrowser.selectedTab.linkedBrowser.contentWindow == observer.window) {
        if (observer.window.document.readyState == "complete") {
            //clifox.print({"m":"w","a":["notifyMutations",records.length]});
            var r = [];
            var t = [];
            for (var i = 0; i < records.length; i++) {
                if (t.indexOf(records[i].target) < 0) {
                    r.push(clifox.getDocJson(records[i].target));
                    t.push(records[i].target);
                }
            }
            clifox.print(JSON.stringify({
                "m": "ec",
                "a": [r],
                "t": "mutation",
                "i": ""
            }));
        }
    }
}
clifox.mutationObsObj = {
    add: function(w) {
        w.mo = w.MutationObserver(clifox.notifyMutations);
        w.mo.observe(w.document, {
            "childList": 1,
            "attributes": 1,
            "characterData": 1,
            "subtree": 1
        });
        w.mo.window = w;
    },
    init: function() {
        for (var i = 0; i < gBrowser.tabs.length; i++) {
            var w = gBrowser.tabs[i].linkedBrowser.contentWindow;
            if (w.mo) {
                w.mo.disconnect();
                w.mo = null;
            }
            this.add(w);
        }
    },
    kill: function() {
        for (var i = 0; i < gBrowser.tabs.length; i++) {
            var w = gBrowser.tabs[i].linkedBrowser.contentWindow;
            if (w.mo) {
                w.mo.disconnect();
                w.mo = null;
            }
        }
    }
};
clifox.getDocJson = function(root, func) {
    var grabVars = {
        "A": ["textContent", "href", "title", "name"],
        "INPUT": ["title", "type", "value", "checked", "name", "disabled", "alt", "src"],
        "BUTTON": ["title", "type", "value", "checked", "name", "textContent", "disabled"],
        "TEXTAREA": ["name", "innerHTML", "disabled"],
        "SELECT": ["textContent", "value", "type", "selectedIndex", "disabled", "name"],
        "IMG": ["alt", "src", "title"],
        "LABEL": ["control"]
    }

    function getNode(x, func, ids) {
        var a, at, al, j, i, n, num, gv;
        num = x[1];
        n = x[0];
        a = [];
        a.push(func(n));
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
            var gvl, i;
            gvl = gv.length;
            for (i = 0; i < gvl; i++) {
                a.push(gv[i]);
                a.push(n[gv[i]]);
            }
        }
        return a;
    };
    //var func;
    var ids = {};
    if (!func) {
        if (clifox.inMap(root.firstChild) != null && clifox.inMap(root.lastChild) != null) {
            func = clifox.addMap;
        } else {
            func = clifox.justAddMap;
        }
    }
    //comment this out?
    //func=clifox.justAddMap;
    var atime, w, l, cur, ll, ww, skip, cs, cst, tt, nn;
    l = [];
    atime = clifox.time();
    w = this.getDomList(root);
    ll = w.length;
    ww = [];
    skip = -1;
    for (var i = 0; i < ll; i++) {
        if (skip != -1 && w[i][1] > skip) {
            continue;
        }
        if (skip != -1) {
            skip = -1;
        }
        tt = w[i][0];
        cs = tt.defaultView ? tt.defaultView.getComputedStyle : tt.ownerDocument.defaultView.getComputedStyle;
        //if(tt.offsetWidth==0&&tt.offsetHeight==0)
        //{
        try {
            cst = cs(tt);
        } catch (e) {
            cst = null;
        };
        //cst=null;
        //var elems=["LI","UL"];
        nn = tt.nodeName.toLowerCase();
        //if(nn!="iframe"&&nn!="frame"&&nn!="#document")
        //{
        if (cst && (cst.visibility == 'hidden' || cst.display == 'none')) {
            skip = w[i][1];
            continue;
        }
        //}
        //}
        ww.push(w[i]);
    }
    ll = ww.length;
    for (var i = 0; i < ll; i++) {
        var t, x;
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
}
clifox.mutationObsObj.init();
clifox.killers.push([clifox.mutationObsObj, clifox.mutationObsObj.kill]);
