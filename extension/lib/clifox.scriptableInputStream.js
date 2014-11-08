//constants
const {
    Cc, Ci, Cu, components
} = require("chrome");
//XPCOMUtils, need to make sure this just has the XPCOMUtils object
Cu.import("resource://gre/modules/XPCOMUtils.jsm", this);
//log all errors to console
//this _should pipe communication here to firefox's stdout.
const error = console.log;
/*
 *This holds our RPC protocol.
 *onCommand is called whenever a message arrives, where Command is the appropriate command designator.
 *Designators are usually single letters for space-saving reasons.
 */

function clifoxJsonRpc(handler) {
    error("clifox:js:clifoxJsonRpc", "handler", handler);
    this.gid = 0;
    this.handler = handler;
    this.map = {};
    this.rMap = {};
    this.gctx = this.handler.gContext;
    error("clifox:js:gbl", "gctx", this.gctx);
    this.map['jthis'] = {
        "name": "clifoxJsGlobalMap",
        "parent": "",
        "id": "jthis",
        "value": this.handler.sb
    };
};
clifoxJsonRpc.prototype = {
    mapNewId: function() {
        this.gid += 1;
        return "j" + this.gid;
    },
    complexTypes: {
        "function": "",
        "object": "",
        "array": ""
    },
    convertArgs: function(list, positions) {
        //if no `positions` or id list, we do nothing, and leave the outer function to deal with `list`
        if (!positions) {} else {
            for (var i = 0; i < positions.length; i++) {
                var where;
                where = positions[i];
                list[where] = this.map[list[where]].value;
            }
        }
    },
    onT: function(o) {
        this.handler.writeJ({
            "m": "echo",
            "a": [JSON.stringify(o)],
            "t": "string"
        });
    },
    /*all methods have:
     *m:string message type,
     *i:string id of the object in which this call is to be referenced [1]
     *a:array of arguments for this call
     *[1]:if we're doing a get into the js side,, i holds the id of the class holding the value we want
     *so get gBrowser.tabs would have the id of gBrowser
     */
    /*
     *g get
     *return a child (by name) of a parent object
     *a:name of child
     */
    onG: function(o) {
        var parentId, parentObject, name, v;
        name = o.a[0];
        parentId = o.i;
        //if parent not found, use top-level object
        if (!(parentId && parentId in this.map)) {
            parentId = "jthis";
        }
        parentObject = this.map[parentId];
        error("clifox:js:get", parentObject, parentObject.value);
        try {
            v = parentObject.value[name];
        } catch (e) {
            throw new Error(e);
        };
        error("clifox:js:getVal", name, v);
        this.sendObject(v, parentObject, name);
    },
    /*
     *s set
     *set parentObject.name to value
     *a:[name,value]
     *oi:positions in a[1]
     *if a[1] is string, [a[1]] will be passed to fix ids
     */
    onS: function(o) {
        var parentId, parentObject, name, val, v, unlist;
        val = o.a[1];
        this.convertArgs(val, o.oi);
        val = val[0];
        name = o.a[0];
        parentId = o.i;
        //if parent not found, use top-level object
        if (!(parentId && parentId in this.map)) {
            parentId = "jthis";
        }
        parentObject = this.map[parentId];
        try {
            v = (parentObject.value[name] = val);
        } catch (e) {
            throw new Error(e);
        };
        this.sendObject(v, parentObject, name);
    },
    /*
     *c call
     *call function with given arguments
     *a:[name,[arg1,arg2,...]]
     *oi:integers corresponding with the positions, in o.a[1], of javascript references
     */
    onX: function(d) {
        try {
            rv = Cu.evalInSandbox(d.a[0], this.handler.sb);
        } catch (e) {
            return this.onError(e);
        }
        this.sendObject(rv, this.map['jthis'], "evalResult");
    },
    onD: function(o) {
        var l, target, id, i;
        if (o.i && (o.i in this.map)) {
            id = o.i;
        } else {
            id = "jthis";
        }
        target = this.map[id].value;
        l = [];
        for (i in target) {
            l.push(i);
        }
        this.handler.writeJ({
            "t": "array",
            "m": "b",
            "a": [l],
            "oi": []
        });
    },
    onC: function(d) {
        var o, id, name, args, rv, parentId;
        //name,[args]?
        if (d.a.length > 1) {
            this.convertArgs(d.a[1], d.oi);
        }[name, args] = d.a;
        if (d.i && d.i in this.map) {
            parentId = d.i;
        } else {
            parentId = "jthis";
        }
        o = this.map[parentId];
        try {
            rv = o.value[name].apply(o.value, args);
        } catch (e) {
            throw new Error(e);
        }
        this.sendObject(rv, o, name);
    },
    sendObject: function(obj, parent, name) {
        var id;
        if (typeof(obj) in this.complexTypes) {
            //not primative, so it'll have to be dealt with through the map
            id = null;
            if (obj['$clifox']) {
                //preexisting object in the map?
                id = obj['$clifox'];
            }
            if (!id && this.rMap[obj]) {
                id = this.rMap[obj];
            } else {
                //create a new map entry for this object
                id = this.mapNewId();
                error("clifox:js:newId", id);
                this.map[id] = {
                    "name": name,
                    "value": obj,
                    "parent": parent,
                    "id": id
                };
                try {
                    obj['$clifox'] = id;
                } catch (e) {
                    this.rMap[obj] = id;
                }
            }
        } else {
            //basic object, send as is
            error("clifox:js:send object as basic", obj);
            id = "";
        }
        //we send object via "a" value
        //we send [id] for a if we're dealing with a complex value
        //we send [0] in oi if we're dealing with a complex value, as the first element in a is then an id reference
        //m=b|back, return data to call
        //t=objectType, used to determine how to treat the returned object
        //i=objectId, the id of the object in our map
        //if i is empty or null, then the type of object is a primative
        this.handler.writeJ({
            "m": "b",
            "t": typeof(obj),
            "i": id,
            "a": [(id ? id : obj)],
            "oi": id ? [0] : []
        });
    },
    onUnknown: function(o) {
        o = {
            "m": "e",
            "a": ["unknown method", o],
            "t": typeof(o)
        };
        this.handler.writeJ(o);
    },
    onError: function(o) {
        this.handler.writeJ({
            "m": "e",
            "a": [o.toString()],
            "t": "string"
        });
    },
}; //handler!

function clifoxJsonHandler(s, gContext) {
    var sbPrototype;
    this.s = s;
    this.temp = "";
    this.gContext = gContext;
    sbPrototype = {
        "clifoxT": this,
        "clifoxO": clifoxJsonRpc,
        "what": "who",
    };
    this.sb = Cu.Sandbox(Cc["@mozilla.org/systemprincipal;1"].createInstance(Ci.nsIPrincipal), {
        "sandboxName": "clifoxSandbox",
        "sandboxPrototype": sbPrototype,
        "wantXrays": true,
        "wantComponents": true,
        "wantXHRConstructor": true
    });
    Cu.evalInSandbox("this.clifox=new clifoxO(clifoxT);clifoxA=clifoxT=null", this.sb);
    this.sb.sb = this.sb;
    sbPrototype = null;
    this.dispatcher = this.sb.clifox;
    //this.dispatcher=new clifoxJsonRpc(this);
}
clifoxJsonHandler.prototype = {
    QueryInterface: XPCOMUtils.generateQI([Ci.nsISupports]),
    writeReal: function(t, l) {
        l = l ? l : t.length;
        this.out.write(t, l);
        this.out.write("\n", 1);
        return l;
    },
    writeJ: function(o) {
        var t;
        t = JSON.stringify(o);
        return this.writeReal(t, t.length);
    },
    write: function(o) {
        if (typeof(o) != "string") {
            return this.writeJ(o);
        }
        this.writeReal(o, o.length);
    },
    init: function(fh) {
        this.out = this.s.outList[this.s.outList.length - 1];
        this.in = this.s.inList[this.s.inList.length - 1];
//~        this.in .QueryInterface(Ci.nsIConverterInputStream);
        this.in .QueryInterface(Ci.nsIScriptableInputStream);
        this.writeJ({
            "m": "w",
            "a": ["hello"]
        });
    },
    start: function(fh) {},
    data: function(fh, len) {
error("clifox:js:data:start");
        error("x", len);
        //buffer holds parcially received command
        var t, v, buffer, where, commands, dl, o;
        t = {};
        buffer = this.temp;
        //error(fh);
        //dump(fh);
        o = {};
        error("read");
//        this.in .readString(len, o);
        o=this.in.readBytes(len);
//        t = o;
        error("read done");
        v = o;
        error("clifox:js:data:v", len, "|" + v + "|");
        if (buffer) {
            v = buffer + v;
        }
        commands = v.split("\n");
        if (commands[commands.length - 1] != "") {
            //strip the last entry from commands, placing it in this.temp for use during the next call
            this.temp = commands.pop();
        } else {
            //or if the last command is blank, just remove it from the commands list
            commands.pop();
            this.temp = "";
        }
        dl = this.dispatcher;
        error(JSON.stringify(commands));
        error("\n");
        for (var i = 0; i < commands.length; i++) {
            var j, t;
            t = commands[i].trim();
            error("clifox:js:command", "commandRaw", "|" + t + "|");
            try {
                j = JSON.parse(t);
            } catch (e) {
                dl.onError(e);
                continue;
            }
            try {
                var m;
                m = j['m'];
                if (m) {
                    m = m.charAt(0).toUpperCase() + m.substr(1);
                }
                if (!m || !dl['on' + m]) {
                    dl.onUnknown(j);
                } else {
                    try {
                        var f;
                        f = dl['on' + m];
                        error("clifox:js:handler", f);
                        //this.writeJ({"m":"echo","a":[j]});
                        f.apply(dl, [j]);
                    } catch (e) {
                        dl.onError(e);
                    }
                }
            } catch (e) {
                error("clifox:js:objError", "error", e.toString());
            }
        } //dispatch loop
error("clifox:js:data:stop");
    },
    stop: function() {
        var w, sl;
        error("clifox:js:clifoxJsonHandler", "stop");
        this.dispatcher = null;
        Cu.nukeSandbox(this.sb);
        this.sb = null;
        sl = this.s.clifox.sessions;
        w = sl.indexOf(this.s);
        if (w > -1) {
            error("clifox:js:removeingSession", w);
            sl.splice(w, 1);
        }
    },
}; //handler

function socketHandler(sOpts, protocol, ipOrPath, port) {
    //s is the session which will be accessed by this socket
    //ipOrPath is the socket filename or ip address
    //the ip address is just to denote listening on localhost
    //you _can _not specify an actual ip address to listen here
    //the serverSocket IDL has noscript set on the initWithAddress call
    //port is the port to listen on, if this is for tcp
    if (!port) {
        port = 4242;
    } else {
        port = parseInt(port);
    }
    this.sOpts = sOpts;
    this.serverSocket = Cc['@mozilla.org/network/server-socket;1'].createInstance(Ci.nsIServerSocket);
    error("clifox:js:socketHandler", "protocol", protocol);
    if (protocol == "tcp") {
        var loopbackOnly, flags;
        loopbackOnly = 1;
        flags = this.serverSocket.KeepWhenOffline;
        //provide localhost or 127.0.0.1 to lsiten only on the loopback interface
        //otherwise, listen on all addresses
        if (!(ipOrPath.indexOf("localhost") > -1 || ipOrPath.indexOf("127.0.0.1") > -1)) {
            loopbackOnly = 0;
        }
        if (loopbackOnly) {
            flags |= this.serverSocket.LoopbackOnly;
        }
        error("clifox:js:socketHandler", "initServerSocket", port, flags, -1);
        this.serverSocket.initSpecialConnection(port, flags, -1);
    } else if (protocol == "socket") {
        var f, perms;
        perms = 0600;
        f = Ci["@mozilla.org/file/local;1"].createInstance(Ci.nsILocalFile);
        f.initWithPath(ipOrPath);
        if (f.exists()) {
            error("clifox:js:socketHandler", "file already exists, can not create socket", f);
        }
        error("clifox:js:socketHandler", "initWithPath", f, perms, -1);
        this.serverSocket.initWithPath(f, perms, -1);
    } else {
        error("clifox:js:socketHandler", "invalid protocol", protocol);
    }
    error("clifox:js:socketHandler", "asyncListen", this);
    this.serverSocket.asyncListen(this);
}
socketHandler.prototype = {
    QueryInterface: XPCOMUtils.generateQI([Ci.nsIServerSocketListener]),
    onSocketAccepted: function(serv, transport) {
        error("clifox:js:socketHandler:onSocketAccepted", transport);
        //new client
        var so;
        so = this.sOpts;
        //initialize a session
        s = new clifoxSession(so['clifox']);
        //add a handler to that session
        s.handler = new so['handler'](s, so['global']);
        //add that session to the global sessions list
        so['clifox'].sessions.push(s);
        s.pipe = transport;
        var inStream, outStream, inStreamJs, outStreamJs, inStreamConverter;
        inStream = transport.openInputStream(0, 0, 0);
//~        inStreamConverter = Cc['@mozilla.org/intl/converter-input-stream;1'].createInstance(Ci.nsIConverterInputStream);
//~        inStreamConverter.init(inStream, 'UTF-8', 1024, Ci.nsIConverterInputStream.DEFAULT_REPLACEMENT_CHARACTER);
        outStream = transport.openOutputStream(0, 0, 0);
        inStreamJs = Cc["@mozilla.org/scriptableinputstream;1"].createInstance(Ci.nsIScriptableInputStream);
        inStreamJs.init(inStream);
        s.inList.push(inStreamJs);
//~        s.inList.push(inStream);
//        this.s.inList.push(inStreamConverter);
//~        s.clifox.initAsyncHandler(s, inStreamConverter, outStream, inStream);
        s.clifox.initAsyncHandler(s, inStreamJs, outStream, inStream);
    },
    onStopListening: function(serv, status) {
        error("clifox:js:socketHandler:onStopListening", status);
        //the entire server socket just died
    },
} //socketHandler

function pumpListener(s) {
    error("clifox:js:pumpListener", "running pump listener");
    this.s = s;
    this.ctx = this.s.handler;
    this.ctx.init();
};
pumpListener.prototype = {
    QueryInterface: XPCOMUtils.generateQI([Ci.nsIStreamListener, Ci.nsIRequestObserver]),
    onDataAvailable: function(request, context, inputStream, offset, count) {
        error("onDataAvailable");
        try {
            this.ctx.data(inputStream, count);
        } catch (e) {
            error("clifox:js:onDataAvailable", e);
        }
    },
    onStartRequest: function(request, context) {
        error("onStartRequest");
        try {
            this.ctx.start();
        } catch (e) {
            error("clifox:js:onStartRequest", e);
        }
    },
    onStopRequest: function(request, context, status) {
        error("onStopRequest", request.status);
        this.ctx.stop();
    },
}; //pump listener prototype

function clifoxSession(cf) {
    //holds functions for data pushing and pulling
    //will send data to this.handler
    this.listener = null;
    //the endpoint, socket|file, that is specific to this session+client pare
    //we should be able to do something like
    //this.outList[this.outList.length-1].write("string\n");
    //and the set of fileStreams or transformers or whatnot will write to this.pipe
    this.pipe = null;
    pipe: null,
    //base clifox object
    this.clifox = cf ? cf : null;
    //uri of original location from which to pull and push rpc
    this.uri = null;
    //we pull from this
    this.inList = [];
    //we push to this
    this.outList = [];
    //this object deals with all inbound/outbound data once it's gotten past sockets, files, everything else
    //handler.initAsyncHandler is to be called on startup of the handler
    //which is to be created on creation of a listening socket, file, or object that can deliver data to handler
    //handler is going to be quite large
    //and deals with all processing of data, such as window monitoring, tab control, etc
    //handler is basically the interface that will feed us data
    this.handler = null;
}
clifoxSession.prototype = {};

function clifox() {
    this.servers = [];
    this.sessions = [];
}
clifox.prototype = {
    listen: function(fullUri, handler, globalContext) {
        //start listening to a particular socket file, tcp connection, etc
        //handler is the handler to initialize when this function is complete
        var protocol, uri, acceptedProtocols;
        acceptedProtocols = ["socket", "tcp"];
        uri = fullUri;
        /*
         *fullUri can be:
         *tcp://hostname:port
         *socket:///path/to/path
         */
        protocol = uri.split(":")[0];
        if (acceptedProtocols.indexOf(protocol) == -1) {
            error("clifox:js:listen", "uri protocol not supported", protocol);
        }
        //s=new clifoxSession(this);
        //s.uri=uri;
        //s.handler=new handler(s,globalContext);
        error("clifox:js:setup", "protocol", protocol);
        if (protocol == "tcp" || protocol == "socket") {
            var sh = this.setupSocket({
                "clifox": this,
                "handler": handler,
                "global": globalContext
            }, uri);
            this.servers.push(sh);
        }
    },
    setupSocket: function(sOpts, uri) {
        var protocol, host, port, i;
        [protocol, host] = uri.split("://");
        port = null;
        if (protocol == "tcp") {
            host = host.replace("/", "");
            if (host.indexOf(":") > -1) {
                [host, port] = host.split(":");
            } else {
                port = null;
            }
        }
        error("running socketHandler", "protocol", protocol, "host", host, "port", port);
        var sh = new socketHandler(sOpts, protocol, host, port);
        return sh;
    },
    initAsyncHandler: function(s, inStream, outStream, pumpInStream) {
        //tested this, I'm not nuts.
        //pump uses the raw nsITransport stream, while the rest of the script uses the scriptableInput stream
        //we can use the output stream from js, though
        //logical to someone, I presume
        s.inList.push(inStream);
        s.outList.push(outStream);
        s.listener = new pumpListener(s);
        s.pump = Cc["@mozilla.org/network/input-stream-pump;1"].createInstance(Ci.nsIInputStreamPump);
        s.pump.init(pumpInStream ? pumpInStream : inStream, -1, -1, 0, 0, false);
        error("clifox:js:initAsyncHandler", "s", s, "s.listener", s.listener, "s.handler", s.handler);
        s.pump.asyncRead(s.listener, null);
        return s;
    },
} //end clifox prototype
//var gCtx = Cc["@mozilla.org/appshell/appShellService;1"]
//.getService(Ci.nsIAppShellService)
//.hiddenDOMWindow.wrappedJSObject;
var c = new clifox(); /*socket|file,unusedGlobalContext*/
c.listen("tcp://0.0.0.0:4242/", clifoxJsonHandler, null);
