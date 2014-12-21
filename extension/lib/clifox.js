//constants
const {
    Cc, Ci, Cu, components
} = require("chrome");
//XPCOMUtils, need to make sure this just has the XPCOMUtils object
Cu.import("resource://gre/modules/XPCOMUtils.jsm", this);
//log all errors to console
//this _should pipe communication here to firefox's stdout.
const error = console.log;
error("clifox startup");
/*
 *This holds our RPC protocol.
 *onCommand is called whenever a message arrives, where Command is the appropriate command designator.
 *Designators are usually single letters for space-saving reasons.
 */

function clifoxJsonRpc(handler) {
//error("clifox:js:clifoxJsonRpc", "handler", handler);
    this.gid = 0;
    this.handler = handler;
    this.map = {};
    this.rMap = [];
    this.gctx = this.handler.gContext;
//error("clifox:js:gbl", "gctx", this.gctx);
    this.map['jthis'] = {
        "name": "clifoxJsGlobalMap",
        "parent": "",
        "id": "jthis",
        "value": this.handler.sb
    };
this.handler.sb['$clifox']='jthis';
};
clifoxJsonRpc.prototype = {
/*clifoxJsonRPC
*bridges javascript access to any javascript type over JSON
*sends primative types like ints and strings directly
*saves complex types like objects and arrays on the javascript side, assigning a unique ID to each,
*and sends that id across to act as a proxy for the object
*the object, it's parent (or the global proxy object if no parent), the type of the object, and the name of the object,
*are saved into map, with the object id as the key.
*each sent object is assigned the above id with the property name "$clifox"
*e.g. obj['$clifox'] would return the id for obj, if obj had been previously sent
*if such assignation does not take, because of the backend js system, a native component, etc,
*an id is generated, and [id,object] is appended to the reverse map, rMap.
*/
    mapNewId: function() {
        this.gid += 1;
        return "j" + this.gid;
    },
    complexTypes: {
        "function": "",
        "object": "",
        "array": ""
    },
/*
*determine if object is in map, and return it's id if so
*/
    inMap: function(obj) {
        var where, rm, c;
//error("xx:inMap",obj);
try {
        where = obj['$clifox'];
} catch(e) {
where=null;
}
        //clifox.print({"m":"w","a":["inMap",obj.toString()]});
        if (where) {
            return where;
        }
        rm = this.rMap;
        for (i = 0; i < rm.length; i++) {
            if (rm[i][1] === obj) {
                return rm[i][0];
            }
        }
        return null;
    },
/*add obj to the map,
*or use the existing obj if it is in the map,
*and return the id for obj
*/
    addMap: function(obj, opts) {
//error("xx:addMap",obj,opts);
//        error({"m":"w","a":clifox.inMap.toString()});
        var x,newAddition;
newAddition=0;
        x = this.inMap(obj);
    if(!x) {
        x=this.justAddMap(obj, opts);
//error("xx:addMap","justAddMapGaveMeId",x);
newAddition=1;
}
//error("xx:addMap","loggingObjStatement");
//error("xx:addMap:",x,"new:"+newAddition.toString(),obj,JSON.stringify(opts));
return x;
    },
    justAddMap: function(obj, opts) {
//error("xx:justAddMap",obj,opts);
        var d, i, parent, name, flag;
        i = this.mapNewId();
//error("xx:justAddMap","got id",i);
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
//error("xx:justAddMap","assigningIdToMap",i,d);
        this.map[i] = d;
//error("xx:justAddMap","assignedIdToMap",i);
        flag = 0;
        try {
            obj['$clifox'] = i;
            if (obj['$clifox']!=i) {
                flag = 1;
            }
        } catch (e) {
            flag = 1;
        }
        if (flag == 1) {
//error("xx:justAddMap","assigningIdToRMap",i,obj);
            this.rMap.push([i,obj]);
        }
//error("xx:justAddMap","returningId",i);
        return i;
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
//error("clifox:js:get", "parentId",parentId,"parentObject",parentObject, "parentObjectValue", parentObject.value);
//parentObjectValue=parentObject.value;
//error("clifox:js:get","name",name,"object",parentObjectValue,"value?",parentObjectValue[name]);
        try {
            v = parentObject.value[name];
//error("clifox:js:get","value",v);
        } catch (e) {
            throw new Error(e);
        };
//error("clifox:js:getVal", name, v);
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
     *x execute
     *eval the provided script and return the value
     *return the raw result, JSON'ified, bypassing proxy, if the result is not an "object"
     *this supports bulk complex data transfer out from js
     */
    onX: function(d) {
        try {
            rv = Cu.evalInSandbox(d.a[0], this.handler.sb, '1.8', "clifox.eval", 1);
        } catch (e) {
            return this.onError(e);
        }
        if (d.a.length == 1) {
            this.handler.writeJ({
                "m": "b",
                "a": [rv],
                "i": "",
                "t": typeof(rv)
            });
        } else {
            this.sendObject(rv, this.map['jthis'], "evalResult");
        }
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
    /*
     *c call
     *call function with given arguments
     *a:[name,[arg1,arg2,...]]
     *oi:integers corresponding with the positions, in o.a[1], of javascript references
     */
    onC: function(d) {
        var o, id, name, args, rv, parentId;
        //name,[args]?
        if (d.a.length > 1) {
            this.convertArgs(d.a[1], d.oi);
        }
        [name, args] = d.a;
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
//error("xx:sendObject","obj",obj,"parent",parent,"name",name);
        var id;
        if (typeof(obj) in this.complexTypes&&obj!=null) {
            //not primative, so it'll have to be dealt with through the map
            id = this.addMap(obj, {
                "parent": parent,
                "name": name
            });
//error("xx:sendObject:complexObjectAddedToMapWithId",id);
        } else {
            //basic object, send as is
//error("clifox:js:send object as basic", obj);
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
            "m": "t",
            "a": ["unknown method", o],
            "t": typeof(o)
        };
        this.handler.writeJ(o);
    },
    onError: function(o) {
        this.handler.writeJ({
            "m": "t",
            "a": [o.toString(), o.stack],
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
//error("write:","|"+t+"|");
        this.out.writeString(t, l);
        this.out.writeString("\n", 1);
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
        this. in = this.s.inList[this.s.inList.length - 1];
        //~        this.in .QueryInterface(Ci.nsIConverterInputStream);
        this.out.QueryInterface(Ci.nsIConverterOutputStream);
        this. in .QueryInterface(Ci.nsIScriptableInputStream);
        this.writeJ({
            "m": "w",
            "a": ["hello"]
        });
    },
    start: function(fh) {},
    data: function(fh, len) {
//        error("clifox:js:data:start");
//        error("x", len);
        //buffer holds parcially received command
        var t, v, buffer, where, commands, dl, o;
        t = {};
        buffer = this.temp;
        //error(fh);
        //dump(fh);
        o = {};
//        error("read");
        //        this.in .readString(len, o);
        o = this. in .readBytes(len);
        //        t = o;
//        error("read done");
        v = o;
//error("clifox:js:data:v", len, "|" + v + "|");
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
//        error(JSON.stringify(commands));
//        error("\n");
        for (var i = 0; i < commands.length; i++) {
            var j, t;
            t = commands[i].trim();
//error("clifox:js:command", "commandRaw", "|" + t + "|");
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
//error("clifox:js:handler", "on"+m);
                        //this.writeJ({"m":"echo","a":[j]});
                        f.apply(dl, [j]);
                    } catch (e) {
                        return dl.onError(e);
                    }
                }
            } catch (e) {
//error("clifox:js:objError", "error", e.toString());
                dl.onError(e);
            }
        } //dispatch loop
//        error("clifox:js:data:stop");
    },
    stop: function() {
        var w, sl,m,i;
error("clifox:js:killing clifox session window");
    Cu.evalInSandbox("clifox.kill();",this.sb);
m=this.dispatcher.map;
for(i in m)
{
try {
if(m[i].value['$clifox'])
{
delete m[i].value['$clifox'];
}
} catch(e) {
}
}
delete this.dispatcher.rMap;
//error("clifox:js:clifoxJsonHandler", "stop");
        this.dispatcher = null;
        this.sb.sb=null;
        Cu.nukeSandbox(this.sb);
        this.sb = null;
        sl = this.s.clifox.sessions;
        w = sl.indexOf(this.s);
        if (w > -1) {
//error("clifox:js:removeingSession", w);
            sl.splice(w, 1);
        }
this.s.kill();
this.s=null;
this.gContext=null;
this.temp=null;
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
//error("clifox:js:socketHandler", "protocol", protocol);
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
//error("clifox:js:socketHandler", "initServerSocket", port, flags, -1);
        this.serverSocket.initSpecialConnection(port, flags, -1);
    } else if (protocol == "socket") {
        var f, perms;
        perms = 0600;
        f = Ci["@mozilla.org/file/local;1"].createInstance(Ci.nsILocalFile);
        f.initWithPath(ipOrPath);
        if (f.exists()) {
//error("clifox:js:socketHandler", "file already exists, can not create socket", f);
        }
//error("clifox:js:socketHandler", "initWithPath", f, perms, -1);
        this.serverSocket.initWithPath(f, perms, -1);
    } else {
//error("clifox:js:socketHandler", "invalid protocol", protocol);
    }
//error("clifox:js:socketHandler", "asyncListen", this);
    this.serverSocket.asyncListen(this);
}
socketHandler.prototype = {
    QueryInterface: XPCOMUtils.generateQI([Ci.nsIServerSocketListener]),
    onSocketAccepted: function(serv, transport) {
//error("clifox:js:socketHandler:onSocketAccepted", transport);
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
        outStreamConverter = Cc['@mozilla.org/intl/converter-output-stream;1'].createInstance(Ci.nsIConverterOutputStream);
        outStreamConverter.init(outStream, 'UTF-8', 1024, Ci.nsIConverterOutputStream.DEFAULT_REPLACEMENT_CHARACTER);
        s.outList.push(outStream);
        s.clifox.initAsyncHandler(s, inStreamJs, outStreamConverter, inStream);
    },
    onStopListening: function(serv, status) {
//error("clifox:js:socketHandler:onStopListening", status);
        //the entire server socket just died
    },
} //socketHandler

function pumpListener(s) {
//error("clifox:js:pumpListener", "running pump listener");
    this.s = s;
    this.ctx = this.s.handler;
    this.ctx.init();
};
pumpListener.prototype = {
    QueryInterface: XPCOMUtils.generateQI([Ci.nsIStreamListener, Ci.nsIRequestObserver]),
    onDataAvailable: function(request, context, inputStream, offset, count) {
//error("onDataAvailable");
        try {
            this.ctx.data(inputStream, count);
        } catch (e) {
//error("clifox:js:onDataAvailable", e);
        }
    },
    onStartRequest: function(request, context) {
//error("onStartRequest");
        try {
            this.ctx.start();
        } catch (e) {
//error("clifox:js:onStartRequest", e);
        }
    },
    onStopRequest: function(request, context, status) {
//error("onStopRequest", request.status);
        this.ctx.stop();
this.ctx=null;
this.s=null;
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
clifoxSession.prototype = {
kill:function()
{
delete this.inList,this.outList,this.pipe,this.clifox,this.listener,this.pump;
},
};

function clifoxRunner() {
    this.servers = [];
    this.sessions = [];
    this.gui=[];
try {
this.initGuiHandling();
} catch(e) {
error(e.toString());
error(e.stack);
}
}
clifoxRunner.prototype = {
initGuiHandling:function() {
var prompter,c;
c=new this.componentHandler(this);
this.comp=c;
var prompter=new this.prompter(this);
c.register("@mozilla.org/prompter;1",prompter);
c.register("@mozilla.org/embedcomp/prompt-service;1",prompter);
//clifox.comp.unregister();
},
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
//error("clifox:js:listen", "uri protocol not supported", protocol);
        }
        //s=new clifoxSession(this);
        //s.uri=uri;
        //s.handler=new handler(s,globalContext);
//error("clifox:js:setup", "protocol", protocol);
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
//error("running socketHandler", "protocol", protocol, "host", host, "port", port);
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
//error("clifox:js:initAsyncHandler", "s", s, "s.listener", s.listener, "s.handler", s.handler);
        s.pump.asyncRead(s.listener, null);
        return s;
    },
} //end clifox prototype

//-----
//this deals with the difference between modal and tab prompts
//change all prompts to have the appropriate window (tab?) as the first argument
clifoxRunner.prototype.prompterProxy=function(proxy,win)
{
//clifox.print({"m":"e","a":["prompterProxy"]});
var i;
this.proxy=proxy;
this.win=win;
for(i in this.proxy)
{
this[i]=new Function('return function() {return this.proxyMethod("'+i+'",arguments);};')()
}
},
clifoxRunner.prototype.prompterProxy.prototype={
proxyMethod:function(name,args) {
var a,i;
a=[];
//clifox.print({"m":"e","a":["noSuchMethod",name,args]});
for(i=0;i<args.length;i++)
{
a.push(args[i]);
}
if(name!="QueryInterface"){
a.unshift(this.win);
};
return this.proxy[name].apply(this.proxy,a);
},
};
clifoxRunner.prototype.addGui=function(win,elems,extras) {
var g;
g={"elements":elems,
"window":win,
"done":0,
"ret":1,
"extras":extras,
};
this.gui.push(g);
this.notifySessions("gui");
return g;
};
clifoxRunner.prototype.notifySessions=function(m) {
var i,s;
s=this.sessions;
for(i=0;i<s.length;i++) {
s[i].handler.sb.clifox.notify(m);
}
};
clifoxRunner.prototype.removeGui=function(o) {
var i;
for(i=0;i<this.gui.length;i++) {
if(this.gui[i]==o) {
this.gui.splice(i,1);
}
}
};
clifoxRunner.prototype.valueProxy=function(obj,key) {
this.obj=obj;
this.key=key;
Object.defineProperty(this,"value",{
"get":function() {
return this.obj[this.key];
},
"set":function(val) {
this.obj[this.key]=val;
return this.obj[this.key];
},
});
};
clifoxRunner.prototype.valueProxy.prototype={
};
clifoxRunner.prototype.prompter=function(base)
{
this.base=base;
};
clifoxRunner.prototype.prompter.prototype={
QueryInterface:XPCOMUtils.generateQI([Ci.nsISupports,Ci.nsIPrompt,Ci.nsIPromptService,Ci.nsIAuthPrompt,Ci.nsIAuthPrompt2,Ci.nsIPromptFactory]),
getPrompt:function(parent,iid) {
var t;
//clifox.print({"m":"e","a":["getPrompt",parent,iid]});
//throw Cr.NS_ERROR_NOT_IMPLEMENTED;
//return null;
return new this.base.prompterProxy(this,parent);
},
doWait:function(win,elems,skipWait,extras) {
var g;
g=this.base.addGui(win,elems,extras);
if(skipWait)
{
return g;
}
var thread = Cc["@mozilla.org/thread-manager;1"]
                        .getService(Ci.nsIThreadManager)
                        .currentThread; 
while(!g.done) {
thread.processNextEvent(true);
}
return g.ret;
},
alert:function(parent,title,text){
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
]);
},
alertCheck:function(parent,title,text,checkMsg,checkState) {
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
["in","checkbox",checkMsg,checkState],
]);
},
confirm:function(parent,title,text) {
//return true/false
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
]);
},
confirmCheck:function(parent,title,text,checkMsg,checkState) {
//return true/false
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
["in","checkbox",checkMsg,checkState],
]);
},
confirmEx:function(parent,title,text,buttonFlags,button0title,button1title,button2title,checkMsg,checkState) {
//set checkState
//return index of button [0|1|2]
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
["out","flags",buttonFlags,null],
//marked as in because we will be interacting with them, even though the index of the pressed button will be returned, (in other words, no direct interaction with the button object)
["in","button",button0title,null],
["in","button",button1title,null],
["in","button",button2title,null],
["in","checkbox",checkMsg,checkState],
]);
},
prompt:function(parent,title,text,value,checkMsg,checkState) {
//return true/false for okay/cancel
//value,checkState are set before exitting
//this.base.print({"m":"e","a":["prompt","parent",parent,"title",title,"text",text,"value",value,"checkMsg",checkMsg,"checkState",checkState]});
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
//we don't know the text is an exact prompt here, so we make the "text" prompt above a different field
//e.g. prompt("dogs are cool. Do you want a dog? y/n.")
//Do you want a dog? would be the prompt,
//but we don't know that,
//so we just consider the text entry it's own control
["in","text",null,value],
["in","checkbox",checkMsg,checkState],
]);
},
promptUsernameAndPassword:function(parent,title,text,username,password,checkMsg,checkState) {
//return boolean true/false
//set username,password,checkState
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
["in","text","username",username],
["in","password","password",password],
["in","checkbox",checkMsg,checkState],
]);
},
promptPassword:function(parent,title,text,password,checkMsg,checkState) {
//return boolean
//set password,checkState
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
["in","password","password",password],
["in","checkbox",checkMsg,checkState],
]);
},
select:function(parent,title,text,count,selectList,selection) {
//return boolean
//set selection with index from selectList
return this.doWait(parent,[
["out","title",title,null],
["out","text",text,null],
["in","list",selectList,selection],
]);
},
/*async re-calling specific are callback,context,async*/
promptAuth:function(parent,channel,level,authInfo,checkMsg,checkState, callback,context,async) {
return this.doWait(parent,[
["out","text","realm: "+authInfo.realm,null],
["out","text","scheme: "+authInfo.authenticationScheme,null],
!(authInfo.flags&authInfo.NEED_DOMAIN)?["in","text","domain",new this.base.valueProxy(authInfo,"domain")]:null,
!(authInfo.flags&authInfo.ONLY_PASSWORD)?null:["in","text","username",new this.base.valueProxy(authInfo,"username")],
["in","text","password",new this.base.valueProxy(authInfo,"password")],
["in","checkbox",checkMsg,checkState],
],async==true?true:false,{"callback":callback,"context":context});
},
asyncPromptAuth:function(parent,channel,callback,context,level,authInfo,checkMsg,checkState) {
//pass arguments to non-async auth, (must move async specific arguments to the end of the list)
return this.promptAuth(parent,channel,level,authInfo,checkMsg,checkState,callback,context,true);
//return this.doWait(parent,[
/*["out","title",title,null],*/
/*["out","text",text,null],*/
//["in","text","username",authInfo.username],
//["in","password","password",authInfo.password],
//["in","checkbox",checkMsg,checkState],
//["in","callback",null,callback],
//],true);
},
};
clifoxRunner.prototype.factory = function(component) {
this.component=component;
}
clifoxRunner.prototype.factory.prototype={
createInstance: function(outer, iid) {
if (outer != null) {
throw Cr.NS_ERROR_NO_AGGREGATION;
}
//clifox.print({"m":"e","a":["createInstance",iid],"z":"createInstance"});
return this.component.QueryInterface(iid);
},
}; 
clifoxRunner.prototype.uuid=Cc['@mozilla.org/uuid-generator;1'].
getService(Ci.nsIUUIDGenerator).generateUUID;
clifoxRunner.prototype.componentHandler=function(base)
{
this.base=base;
this.components=[];
this.componentRegistrar = components.manager
.QueryInterface(Ci.nsIComponentRegistrar);
}
clifoxRunner.prototype.componentHandler.prototype={
register:function(contractId,component) {
var cid,factory;
//insure contract we are calling exists
cid = this.componentRegistrar
.contractIDToCID(contractId);
cid=this.base.uuid();
factory=new this.base.factory(component);
this.componentRegistrar.registerFactory(cid,"clifox.override."+contractId,contractId,factory);
this.components.push([contractId,cid,factory]);
},
unregister:function(contractId,cid,factory)
{
var index,i,match,c;
index=-1;
if(contractId)
{
index=0;
match=contractId;
}
if(cid)
{
index=1;
match=cid;
}
if(factory)
{
index=2;
match=factory;
}
for(i=0;i<this.components.length;i++)
{
c=this.components[i];
if((index==-1)||(c[index]==match))
{
//unregister takes [classId,factory]
this.componentRegistrar.unregisterFactory(c[1],c[2]);
}
}
},
};
//-----

var c = new clifoxRunner(); /*socket|file,unusedGlobalContext*/
c.gthis=this;
c.listen("tcp://0.0.0.0:4242/", clifoxJsonHandler, null);
