package {
    import flash.display.*;
    import flash.desktop.NativeApplication;
    import flash.events.*;
    import flash.net.*;
    import flash.system.*;
    import flash.utils.*;

    /**
     * Differential test driver.
     *
     * Loads the SWF named by the `swf` flashvar into an isolated ApplicationDomain
     * and exercises the deterministic logic of GameStrings / GameType /
     * PlayerType / OpponentType.  Results are POSTed to the local collector.
     *
     * Run the same probe against the original SWF and the rebuilt SWF and diff
     * the two reports.
     */
    public class Probe extends Sprite {
        private var out:Array = [];
        private var target:String;

        public function Probe() {
            target = loaderInfo.parameters.swf;
            if (target != null && target != "") { loadTarget(); return; }
            // Under AIR `adl` there are no flashvars, so read the target from a
            // small file next to the app (works in both runtimes).
            var tf:URLLoader = new URLLoader();
            tf.addEventListener(Event.COMPLETE, function(e:Event):void {
                target = strip(String(tf.data)); loadTarget();
            });
            tf.addEventListener(IOErrorEvent.IO_ERROR, function(e:Event):void {
                target = "app:/build/runtime-original/Gazillionaire.swf"; loadTarget();
            });
            try { tf.load(new URLRequest("probe-target.txt")); }
            catch (e:Error) { target = "app:/build/runtime-original/Gazillionaire.swf"; loadTarget(); }
        }

        private function strip(s:String):String {
            return s.replace(/^[\s\r\n]+/, "").replace(/[\s\r\n]+$/, "");
        }

        private function loadTarget():void {
            out.push("target=[" + target + "]");
            var iso:Boolean = loaderInfo.parameters.isolated != "0";
            var dom:ApplicationDomain = iso ? new ApplicationDomain(null)
                                            : ApplicationDomain.currentDomain;
            var ctx:LoaderContext = new LoaderContext(false, dom);
            var l:Loader = new Loader();
            l.contentLoaderInfo.addEventListener(Event.COMPLETE, onDone);
            l.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, function(e:IOErrorEvent):void {
                out.push("IOERROR " + target); report();
            });
            try { l.load(new URLRequest(target), ctx); }
            catch (e:Error) { out.push("LOADERR " + e.message); report(); }
        }

        private function onDone(e:Event):void {
            var ad:ApplicationDomain = (e.target as LoaderInfo).applicationDomain;
            // Flex kicks off the SystemManager only once the loaded root is on
            // the display list; class script-inits can be deferred until then.
            try {
                var content:* = (e.target as LoaderInfo).content;
                if (content is DisplayObject && content.parent == null) addChild(content);
            } catch (e9:Error) { }
            setTimeout(function():void { runTests(ad); }, 1500);
        }

        private function runTests(ad:ApplicationDomain):void {
            var names:Array = ["GameStrings", "GameType", "PlayerType", "OpponentType",
                               "Gazillionaire", "LoadScreen", "CustomPreloader",
                               "mx.core.UIComponent", "flash.utils.ByteArray"];
            var found:Array = [];
            for each (var nm:String in names) {
                try { var cl:Class = ad.getDefinition(nm) as Class;
                      found.push(nm + "=" + (cl != null)); }
                catch (e1:Error) { found.push(nm + "=EX:" + e1.message.substr(0, 20)); }
            }
            out.push("defs " + found.join(" "));
            try {
                var GSC:Class = ad.getDefinition("GameStrings") as Class;
                var GTC:Class = ad.getDefinition("GameType") as Class;
                var PTC:Class = ad.getDefinition("PlayerType") as Class;
                var OPC:Class = ad.getDefinition("OpponentType") as Class;
                var gs:Object = new GSC();
                gs.initialize();
                testStrings(gs);
                testOpponent(OPC, gs);
                var p:Object = testPlayer(PTC);
                var game:Object = testGame(GTC, PTC, OPC, gs, p);
                testMechanics(ad, gs);
                testTrading(ad, game);
            } catch (err:Error) {
                out.push("ERR " + err.message);
            }
            report();
        }

        // ---- tests -------------------------------------------------------

        private function testStrings(gs:Object):void {
            var keys:Array = [];
            for (var k:String in gs.strings) keys.push(k);
            keys.sort();
            var h:uint = 5381, total:int = 0;
            for each (var kk:String in keys) {
                var v:String = gs.strings[kk];
                total += v.length;
                h = (h * 33 + hashStr(kk + "=" + v)) >>> 0;
            }
            out.push("GameStrings keys=" + keys.length + " charlen=" + total + " hash=" + h);
            out.push("GameStrings getString(kilo_letter)=" + gs.getString("kilo_letter"));
            out.push("GameStrings getString(missing)=" + gs.getString("__nope__"));
        }

        private function testOpponent(OPC:Class, gs:Object):void {
            var o:Object = new OPC();
            o.init(3, 4, gs);
            var b:ByteArray = new ByteArray();
            o.serialize(b);
            out.push("OpponentType.ser len=" + b.length + " hash=" + bytesHash(b));
        }

        private function testPlayer(PTC:Class):Object {
            var p:Object = new PTC();
            p.init(3, 4);
            // neutralise the three f_rnd-derived fields
            p.age = 30; p.insuranceCost = 5000; p.random = 50;
            var b:ByteArray = new ByteArray();
            p.serialize(b);
            out.push("PlayerType.ser len=" + b.length + " hash=" + bytesHash(b));
            // deserialize round-trip
            b.position = 0;
            var p2:Object = new PTC();
            p2.deserialize(b);
            var b2:ByteArray = new ByteArray();
            p2.serialize(b2);
            out.push("PlayerType.roundtrip hash=" + bytesHash(b2));
            return p;
        }

        private function testGame(GTC:Class, PTC:Class, OPC:Class, gs:Object, p:Object):Object {
            var g:Object = new GTC();
            g.playerNumberOf = 2;
            g.opNumberOf = 2;
            var p2:Object = new PTC(); p2.init(3, 4); p2.age = 31; p2.insuranceCost = 5001; p2.random = 51;
            g.p = [p, p2];
            var o1:Object = new OPC(); o1.init(1, 1, gs);
            var o2:Object = new OPC(); o2.init(2, 2, gs);
            g.o = [null, o1, o2];
            g.advertC = flat(7, 1.5);
            g.fuelCost = flat(7, 2.5);
            g.planetIndex = iflat(7, 3);
            g.planetX = iflat(7, 4);
            g.planetY = iflat(7, 5);
            g.playerOrder = iflat(4, 1);
            g.stockCrash = bflat(7);
            g.stockTrend = iflat(7, 50);
            g.stockPrice = mat2(7, 16, 100.0);
            g.comR = mat3(7, 3, 6, 10.0);
            g.comP = mat3(7, 3, 6, 20.0);
            g.comA = mat3(7, 3, 6, 30.0);
            g.activateTurn = 1; g.activateZinn = 2; g.activateSupply = 3; g.activateLoan = 4;
            g.activateInsurance = 5; g.activateViewCity = 6; g.activateFuel = 7;
            g.activatePassengers = 8; g.activateCrew = 9; g.activateAdvertising = 10;
            g.activateTax = 11; g.activateBank = 12; g.activateWarehouse = 13;
            g.activateExplore = 14; g.activateDistance = 15; g.activateFacility = 16; g.activateStock = 17;
            g.auction = 0; g.auctionLast = 0; g.auctionCompany = 0; g.auctionNextCompany = 0;
            g.auctionCompanyLast = 0; g.auctionNextCompanyLast = 0;
            g.auctionHighBid = 0; g.auctionNextBid = 0; g.auctionHighBidLast = 0; g.auctionNextBidLast = 0;
            g.auctionFacilityType = 0; g.auctionFacilityPlanet = 0; g.auctionFacilityFee = 0;
            g.auctionFacilityTypeLast = 0; g.auctionFacilityPlanetLast = 0; g.auctionFacilityFeeLast = 0;
            g.difficulty = 2; g.dateYear = 139; g.exportTariff = 2; g.fuelPriceRange = 200;
            g.game = 1; g.gameEvent = 0; g.importTariff = 3; g.isMidTurn = false; g.level = 3;
            g.news = 5; g.newsData = 6; g.newsPlanet = 2; g.passTax = 15; g.player = 0;
            g.playerTurnCounter = 7; g.sellingProfit = 1.25; g.stockFlag = true;
            g.turn = 3; g.tutor = false; g.weather = 5; g.weatherPlanet = 2;
            g.winner = -1; g.winningPoint = 5000000;
            var b:ByteArray = g.serialize() as ByteArray;
            out.push("GameType.ser len=" + b.length + " hash=" + bytesHash(b));
            b.position = 0;
            var g2:Object = new GTC();
            g2.deserialize(b);
            var b2:ByteArray = g2.serialize() as ByteArray;
            out.push("GameType.roundtrip hash=" + bytesHash(b2));
            return g;
        }

        // ---- helpers -----------------------------------------------------

        private function testMechanics(ad:ApplicationDomain, gs:Object):void {
            var FG:Class = ad.getDefinition("mx.core.FlexGlobals") as Class;
            var app:Object = FG.topLevelApplication;
            if (app == null) throw new Error("loaded Flex application is not ready");
            app.currentStrings = gs;
            out.push("Mechanics.xml=" + app.xmlUnescape("&lt;x&gt;&quot;a&quot;&apos;b&apos;&amp;"));
            var results:Array = [];
            for each (var amount:Number in [-500001, -50000, 0, 49999, 50000, 999999, 1000000]) {
                results.push(app.status_name(amount));
            }
            out.push("Mechanics.status hash=" + hashStr(results.join("|")));
            results = [];
            for (var tier:int = 0; tier < 3; tier++) {
                for (var item:int = 0; item < 6; item++) results.push(app.commodity_sound(tier, item));
            }
            out.push("Mechanics.commoditySound hash=" + hashStr(results.join("|")));
        }

        private function testTrading(ad:ApplicationDomain, g:Object):void {
            var FG:Class = ad.getDefinition("mx.core.FlexGlobals") as Class;
            var app:Object = FG.topLevelApplication;
            app.sound_enabled = false;
            app.g = g;
            var p:Object = g.p[g.player];
            p.cash = 100000; p.cargoTons = 0; p.cargoCapacity = 100;
            p.quickBuy = true;
            // The nested SWF's full document UI is not initialized by AIR.
            // Supply real Flex controls to exercise the original handlers;
            // this is a handler fixture, not a rendered-session test.
            var description:XML = describeType(app);
            for each (var accessor:XML in description.accessor) {
                var name:String = String(accessor.@name);
                if (name.indexOf("frm_Market_") == 0 && app[name] == null) {
                    var CC:Class = ad.getDefinition(String(accessor.@type)) as Class;
                    app[name] = new CC();
                }
            }
            app.frm_Market_load();
            var buttonY:Number = app.frm_Market_button_view_all.y;
            app.frm_Market_refresh_grid(0);
            if (app.frm_Market_button_view_all.y != buttonY ||
                app.frm_Market_button_view_selected1.y != buttonY - 1) {
                throw new Error("market selection marker moved the source button");
            }
            app.frame_globals[109] = 0;
            app.frame_globals[111] = 0;
            app.frm_Market_buy();
            if (p.cargoTons <= 0 || p.cash >= 100000) throw new Error("trade did not buy cargo");
            out.push("Trading.buy cash=" + p.cash + " cargo=" + p.cargoTons + " hash=" + bytesHash(g.serialize()));
            app.frame_globals[109] = 0;
            app.frame_globals[111] = 0;
            app.frm_Market_sell();
            if (p.cargoTons != 0) throw new Error("trade did not sell cargo");
            out.push("Trading.sell cash=" + p.cash + " cargo=" + p.cargoTons + " hash=" + bytesHash(g.serialize()));
            var bytes:ByteArray = g.serialize(); bytes.position = 0;
            var GC:Class = ad.getDefinition("GameType") as Class;
            var loaded:Object = new GC(); loaded.deserialize(bytes);
            out.push("Trading.roundtrip hash=" + bytesHash(loaded.serialize()));
            // Unique commodity minima force both AI destinations to planet 0;
            // distinct travel times avoid random tie breaking.
            g.p[0].planetLast = 0; g.p[0].planet = 1; g.p[0].engine = 1;
            g.p[1].planetLast = 0; g.p[1].planet = 3; g.p[1].engine = 2;
            g.p[0].travelDelayed = g.p[1].travelDelayed = 1;
            g.o[1].planet = 2; g.o[1].engine = 3;
            g.o[2].planet = 5; g.o[2].engine = 4;
            app.frm_Travel3_travel();
            if (g.playerOrder.join(",") != "7,0,8,1") throw new Error("unexpected travel order");
            out.push("Travel.order=" + g.playerOrder.join(",") + " hash=" + bytesHash(g.serialize()));
            g.o[1].cash = 10000;
            g.o[1].facilityRevenue[0] = 50;
            g.o[2].facilityFee[0] = 300;
            g.p[0].facilityFee[0] = 100; g.p[1].facilityFee[0] = 200;
            app.frm_Travel3_opponentFacilities(1);
            if (g.o[1].cash != 9450) throw new Error("unexpected AI facility payment");
            out.push("AI.facilities cash=" + g.o[1].cash + " hash=" + bytesHash(g.serialize()));
        }

        private function flat(n:int, base:Number):Array {
            var a:Array = []; for (var i:int = 0; i < n; i++) a.push(base + i * 0.5); return a;
        }
        private function iflat(n:int, base:int):Array {
            var a:Array = []; for (var i:int = 0; i < n; i++) a.push(base + i); return a;
        }
        private function bflat(n:int):Array {
            var a:Array = []; for (var i:int = 0; i < n; i++) a.push(i % 2 == 0); return a;
        }
        private function mat2(d1:int, d2:int, base:Number):Array {
            var a:Array = []; for (var i:int = 0; i < d1; i++) a.push(flat(d2, base + i)); return a;
        }
        private function mat3(d1:int, d2:int, d3:int, base:Number):Array {
            var a:Array = []; for (var i:int = 0; i < d1; i++) a.push(mat2(d2, d3, base + i)); return a;
        }
        private function hashStr(s:String):uint {
            var h:uint = 0; for (var i:int = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return h;
        }
        private function bytesHash(b:ByteArray):uint {
            var h:uint = 2166136261; b.position = 0;
            for (var i:int = 0; i < b.length; i++) { h = (h ^ b.readUnsignedByte()) >>> 0; h = (h * 16777619) >>> 0; }
            return h;
        }

        private function report():void {
            var text:String = out.join("\n");
            trace(text);
            try {
                var so:SharedObject = SharedObject.getLocal("gazprobe");
                so.data.out = text; so.flush();
            } catch (e:Error) { }
            try {
                var r:URLRequest = new URLRequest("http://127.0.0.1:8765/report");
                r.method = URLRequestMethod.POST;
                r.data = text;
                var sender:URLLoader = new URLLoader();
                sender.addEventListener(Event.COMPLETE, function(e:Event):void {
                    NativeApplication.nativeApplication.exit(0);
                });
                sender.addEventListener(IOErrorEvent.IO_ERROR, function(e:Event):void {
                    NativeApplication.nativeApplication.exit(1);
                });
                sender.load(r);
            } catch (e:Error) { NativeApplication.nativeApplication.exit(1); }
        }
    }
}
