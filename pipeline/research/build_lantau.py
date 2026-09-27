import json
AF="https://www.hiking.gov.hk/trail/info/id/"
AFCD={1:AF+"YUNwM2czOWpZU2hrTXF3NlRTU3hNZz09",2:AF+"SVdvZDdnTENQZXl0byt5QndsQ0NmZz09",3:AF+"NWJYSHpGd0d5NmZNdXdtQmM4UTBRdz09",4:AF+"bFFXSU03dVRuU1VQSHpMRThST3Zldz09",5:AF+"ckcwQUpQUHEzcWRhZVdDYkZsQlR2UT09",6:AF+"NjVmZUw2OURKcjZkQldxYlN3TjJXQT09",7:AF+"Qk9WL0ZDY2huUFJSYVg4Rm5Gb3h3Zz09",8:AF+"Nk5VMHQ4YmlkMFZkV0JxdDdtSS94Zz09",9:AF+"ZjQ0ZG5zT3FFbm5HYUlwVmNtck5QUT09",10:AF+"YS9XR04yWE5GRnBRZTFFS3E3bjlKdz09",11:AF+"NktmYXJYQWVwNmMrM016d09JbkYrQT09",12:AF+"aU9nYU5ZRzBPU0VIWWJ0NUhkK1NWZz09"}
OAS={1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten",11:"eleven",12:"twelve"}
WIKI="https://en.wikipedia.org/wiki/Lantau_Trail"
NLB="https://www.nlb.com.hk/route/detail/"
CAMP="https://www.afcd.gov.hk/english/country/cou_vis/cou_vis_cam/cou_vis_cam_cam/cou_vis_cam_"
TOI="https://www.afcd.gov.hk/english/country/cou_vis/cou_vis_rec/cou_toi.html"
NEWS="https://www.hiking.gov.hk/news"

def T(mode,route,fe,fz,ne,nz):
    return {"mode":mode,"route":route,"from_en":fe,"from_zh":fz,"note_en":ne,"note_zh":nz}

# reusable transport legs
FERRY_IN=T("ferry","Central–Mui Wo","Central Pier 6","中環6號碼頭","Sun Ferry; about every 30–50 min, ~35–55 min trip. Get off at Mui Wo Ferry Pier.","新渡輪；約30–50分鐘一班，航程約35–55分鐘，於梅窩碼頭下船。")
FERRY_OUT=T("ferry","Mui Wo–Central","Mui Wo Ferry Pier","梅窩碼頭","Sun Ferry to Central Pier 6; about every 30–50 min until late night.","新渡輪往中環6號碼頭；約30–50分鐘一班，服務至深夜。")
B3M_IN=T("bus","NLB 3M","Tung Chung Station Bus Terminus (MTR Tung Chung)","東涌站巴士總站（港鐵東涌站）","Frequent (about every 15–25 min).","班次頻密（約15–25分鐘一班）。")
B3M_OUT=T("bus","NLB 3M","Mui Wo Ferry Pier","梅窩碼頭","To Tung Chung Station; frequent (about every 15–25 min).","往東涌站；班次頻密（約15–25分鐘一班）。")
TAXI_MW=T("taxi","Lantau taxi","Mui Wo","梅窩","Blue Lantau taxis only; may need to wait.","只有藍色大嶼山的士，或需等候。")

def nam_shan(direction):
    if direction=="to":
        return [T("bus","NLB 1, 2, 3M, 4","Mui Wo Ferry Pier (1, 2, 4) / Tung Chung Station (3M)","梅窩碼頭（1、2、4）／東涌站（3M）","Alight at 'Nam Shan Camp Site' stop on South Lantau Road. 3M is the most frequent; 2 and 4 are sparse.","於嶼南道「南山營地」站下車。3M最頻密；2及4號班次疏。")]
    return [T("bus","NLB 1, 2, 3M, 4","Nam Shan Camp Site stop","南山營地站","Towards Mui Wo: 1, 2, 3M, 4. Towards Tung Chung: 3M. Route 1 (Tai O) and 2 (Ngong Ping) go west.","往梅窩：1、2、3M、4；往東涌：3M。1號往大澳、2號往昂坪。")]

PKA_IN=[T("bus","NLB 3M, 11, 23","Tung Chung Station (3M, 11) / Tung Chung Tat Tung Road (23) / Mui Wo (3M)","東涌站（3M、11）／東涌達東路（23）／梅窩（3M）","Alight at 'Pak Kung Au' stop on Tung Chung Road. 3M and 11 are frequent.","於東涌道「伯公坳」站下車。3M及11號班次頻密。")]
PKA_OUT=[T("bus","NLB 3M, 11, 23","Pak Kung Au stop","伯公坳站","Tung Chung side: 3M, 11, 23. Mui Wo side: 3M. Stops on both sides of the road.","往東涌：3M、11、23；往梅窩：3M。路兩旁均有車站。")]
NP_BUS_IN=[T("bus","NLB 23","Tung Chung Tat Tung Road Bus Terminus","東涌達東路巴士總站","About every 20–30 min (Mon–Sat 07:15–18:10).","約20–30分鐘一班（星期一至六07:15–18:10）。"),
           T("bus","NLB 2","Mui Wo Ferry Pier","梅窩碼頭","Sparse: Mon–Fri only 5 trips (11:00–17:00); hourly Sat and Sun/PH.","班次疏：星期一至五只有5班（11:00–17:00）；星期六及日/假期每小時一班。"),
           T("bus","NLB 21","Tai O","大澳","About hourly; last from Tai O ~16:45 Mon–Fri, 17:45 Sat/Sun.","約每小時一班；大澳尾班約16:45（平日）、17:45（週末）。"),
           T("cablecar","Ngong Ping 360","Tung Chung Cable Car Terminal (near MTR Tung Chung)","東涌纜車站（近港鐵東涌站）","About 25 min. 10:00–18:00 weekdays, 09:00–18:30 weekends/PH.","約25分鐘。平日10:00–18:00，週末及假期09:00–18:30。")]
NP_OUT=[T("bus","NLB 23","Ngong Ping Bus Terminus","昂坪巴士總站","To Tung Chung; last bus 19:10.","往東涌；尾班19:10。"),
        T("bus","NLB 2","Ngong Ping Bus Terminus","昂坪巴士總站","To Mui Wo; sparse. Last 19:05 Mon–Fri, 18:10 Sat, 18:45 Sun/PH.","往梅窩；班次疏。尾班：平日19:05、星期六18:10、日/假期18:45。"),
        T("bus","NLB 21","Ngong Ping Bus Terminus","昂坪巴士總站","To Tai O; about hourly, last ~18:15–18:30.","往大澳；約每小時一班，尾班約18:15–18:30。"),
        T("cablecar","Ngong Ping 360","Ngong Ping Cable Car Terminal","昂坪纜車站","To Tung Chung (~25 min). Closes 18:00 weekdays, 18:30 weekends/PH.","往東涌（約25分鐘）。平日18:00、週末及假期18:30關閉。"),
        T("taxi","Lantau taxi","Ngong Ping","昂坪","Blue Lantau taxis; may need to wait.","藍色大嶼山的士，或需等候。")]
SW_IN=[T("bus","NLB 1, 11 / 2, 23 / 21","Mui Wo (1, 2) / Tung Chung (11, 23) / Tai O or Ngong Ping (21)","梅窩（1、2）／東涌（11、23）／大澳或昂坪（21）","Alight at 'Sham Wat Road' (1, 11) or the nearby 'Sham Wat Road Junction' (2, 23). Start is at the pavilion at Sham Wat Rd / Keung Shan Rd junction.","於「深屈道」（1、11）或附近「深屈道口」（2、23）下車。起點在深屈道與羗山道交界涼亭。")]
SW_OUT=[T("bus","NLB 1, 2, 11, 23, 21","Sham Wat Road / Sham Wat Road Junction stops","深屈道／深屈道口站","To Mui Wo: 1, 2. To Tung Chung: 11, 23. To Tai O: 1, 11, 21. To Ngong Ping: 2, 21, 23.","往梅窩：1、2；往東涌：11、23；往大澳：1、11、21；往昂坪：2、21、23。")]
LUNG_OUT=[T("bus","NLB 1, 11, 21","Lung Chai (龍仔) stop, Keung Shan / Tai O Road","羗山道／大澳道「龍仔」站","Walk down from Lung Tsai Ng Yuen along Keung Shan Catchwater. 1 to Mui Wo, 11 to Tung Chung, 21 to Ngong Ping; all also go to Tai O.","由龍仔悟園沿羗山引水道落山。1號往梅窩、11號往東涌、21號往昂坪；亦可往大澳。")]
LUNG_IN=[T("bus","NLB 1, 11","Mui Wo (1) / Tung Chung (11)","梅窩（1）／東涌（11）","Alight at 'Lung Chai'. Walk up Keung Shan Catchwater to Ng Yuen, then along the trail to Man Cheung Po.","於「龍仔」站下車，沿羗山引水道上悟園，再沿鳳凰徑往萬丈布。")]
TAIO_IN=[T("bus","NLB 1, 11, 21","Mui Wo (1) / Tung Chung Station (11) / Ngong Ping (21)","梅窩（1）／東涌站（11）／昂坪（21）","11 is frequent (about every 15–25 min); 1 about every 30–45 min; 21 about hourly.","11號頻密（約15–25分鐘）；1號約30–45分鐘；21號約每小時一班。"),
         T("ferry","Tuen Mun–Tung Chung–Sha Lo Wan–Tai O","Tuen Mun / Tung Chung","屯門／東涌","Fortune Ferry; few sailings a day – check timetable.","富裕小輪；每日班次少，出發前查閱船期。")]
TAIO_OUT=[T("bus","NLB 1, 11, 21","Tai O Bus Terminus","大澳巴士總站","11 to Tung Chung (frequent, till after midnight); 1 to Mui Wo; 21 to Ngong Ping (about hourly, last ~17:45).","11號往東涌（頻密，服務至午夜後）；1號往梅窩；21號往昂坪（約每小時，尾班約17:45）。"),
          T("ferry","Tai O–Sha Lo Wan–Tung Chung–Tuen Mun","Tai O","大澳","Fortune Ferry; few sailings – check timetable.","富裕小輪；班次少，出發前查閱船期。"),
          T("taxi","Lantau taxi","Tai O","大澳","Blue Lantau taxis at Tai O.","大澳有藍色大嶼山的士。")]
SHATSUI=lambda d: [T("bus","NLB 1, 2, 11, 23","Sha Tsui stop (Shek Pik dam, South Lantau Road)","沙咀站（石壁水塘壩，嶼南道）",
    "Towards Tung Chung: 11, 23. Towards Mui Wo: 1, 2. Towards Tai O/Ngong Ping: 1, 11 / 2, 23." if d=="out" else "From Mui Wo: 1, 2. From Tung Chung: 11, 23.",
    "往東涌：11、23；往梅窩：1、2；往大澳／昂坪：1、11／2、23。" if d=="out" else "梅窩開：1、2；東涌開：11、23。")]
SHUIHAU=lambda d: [T("bus","NLB 1, 2, 11, 23","Shui Hau Village (East) stop","水口村(東)站",
    "Towards Mui Wo: 1, 2. Towards Tung Chung: 11, 23." if d=="out" else "From Mui Wo: 1, 2. From Tung Chung: 11, 23. Walk ~2 min along South Lantau Road to the start.",
    "往梅窩：1、2；往東涌：11、23。" if d=="out" else "梅窩開：1、2；東涌開：11、23。下車後沿嶼南道步行約2分鐘到起點。")]
CSB=lambda d: [T("bus","NLB 1, 2, 11, 23 (also 4)","Cheung Sha Bridge stop, South Lantau Road","嶼南道「長沙大橋」站",
    "From post L113 turn right and walk ~20 min down to South Lantau Road. To Mui Wo: 1, 2, 4. To Tung Chung: 11, 23." if d=="out" else "Walk ~50 m to a pavilion, turn left, ~20 min up to post L113.",
    "由標距柱L113右轉步行約20分鐘落嶼南道。往梅窩：1、2、4；往東涌：11、23。" if d=="out" else "下車後沿嶼南道行約50米至涼亭，左轉步行約20分鐘到標距柱L113。")]
LOUK=lambda d: [T("bus","NLB 1, 2, 3M (also 4)","Lo Uk Tsuen stop, South Lantau Road (Pui O)","嶼南道「羅屋村」站（貝澳）",
    "About 1 min walk from trail end. To Mui Wo: 1, 2, 3M, 4. To Tung Chung: 3M." if d=="out" else "From Mui Wo: 1, 2, 3M, 4. From Tung Chung Station: 3M.",
    "終點步行約1分鐘。往梅窩：1、2、3M、4；往東涌：3M。" if d=="out" else "梅窩開：1、2、3M、4；東涌站開：3M。")]

stages=[
dict(n=1,start_en="Mui Wo",start_zh="梅窩",end_en="Nam Shan",end_zh="南山",km=2.5,hours=1,difficulty="Easy (AFCD 1★)",posts=["L001","L005"],posts_estimated=False,
 highlights_en=["Views over Mui Wo's five villages","Shaded road-side path","Nam Shan barbecue area"],
 highlights_zh=["俯瞰梅窩五村","路旁樹蔭小徑","南山燒烤場"],high_point=None,
 water_en="Buy supplies in Mui Wo (shops, restaurants). Nothing en route. Tap water at Nam Shan campsite.",
 water_zh="在梅窩購買補給（商店、餐廳）。沿途無補給。南山營地有自來水。",
 toilets_en="Mui Wo Ferry Pier; flushing toilets at Nam Shan.",toilets_zh="梅窩碼頭；南山有沖水廁所。",
 exits_en=["Short stage beside South Lantau Road – bus stops nearby"],exits_zh=["全段貼近嶼南道，附近有巴士站"],
 to_start=[FERRY_IN,B3M_IN,TAXI_MW],from_end=nam_shan("from"),
 safety_en="Mostly along road with traffic. Stock up in Mui Wo before stage 2.",safety_zh="大部分沿車路，小心車輛。第二段前先在梅窩備足物資。",
 sources=[AFCD[1],WIKI,"https://www.oasistrek.com/lantau_trail_one.php",CAMP+"27_NamShan.html",TOI,NLB+"1"]),
dict(n=2,start_en="Nam Shan",start_zh="南山",end_en="Pak Kung Au",end_zh="伯公坳",km=6.5,hours=3.25,difficulty="Difficult (AFCD 4★)",posts=["L005","L018"],posts_estimated=False,
 highlights_en=["Sunset Peak silvergrass (autumn)","1920s stone cabins of Lantau Mountain Camp","Views of Cheung Sha Beach"],
 highlights_zh=["大東山芒草（秋季）","1920年代石屋（大嶼山石屋營）","遠眺長沙海灘"],
 high_point={"name_en":"Sunset Peak (Tai Tung Shan)","name_zh":"大東山","m":869},
 water_en="None on trail. Carry all water; any stream water must be treated.",water_zh="沿途無補給，須帶足食水；溪水須處理後才飲用。",
 toilets_en="Nam Shan (start) and Pak Kung Au (end, AFCD flushing toilet). None on trail.",toilets_zh="南山（起點）及伯公坳（終點，漁護署沖水廁所）。沿途沒有。",
 exits_en=["Side paths on the left soon after Nam Shan lead down to South Lantau Road"],exits_zh=["離開南山不久，左方有支路可落嶼南道"],
 to_start=nam_shan("to"),from_end=PKA_OUT,
 safety_en="Big climbs and descents; almost no shade; exposed to wind, fog and lightning. Avoid in heat, thunderstorms or strong wind.",
 safety_zh="大上大落；幾乎無遮蔭；山頂當風，易起霧及受雷暴影響。酷熱、雷暴或大風時避免前往。",
 sources=[AFCD[2],WIKI,"https://www.oasistrek.com/lantau_trail_two.php",TOI,"https://www.thruhikinghk.com/the-lantau-trail.html",NLB+"6"]),
dict(n=3,start_en="Pak Kung Au",start_zh="伯公坳",end_en="Ngong Ping",end_zh="昂坪",km=4.5,hours=3,difficulty="Difficult (AFCD 4★)",posts=["L018","L027"],posts_estimated=False,
 highlights_en=["Lantau Peak summit (934 m)","Sunrise and sea-of-cloud views","Steep 'Staircase to the Sky' down to Ngong Ping"],
 highlights_zh=["鳳凰山頂（934米）","日出及雲海","陡峭石級「天梯」落昂坪"],
 high_point={"name_en":"Lantau Peak (Fung Wong Shan)","name_zh":"鳳凰山","m":934},
 water_en="None on trail. Shops and restaurants at Ngong Ping Village at the end.",water_zh="沿途無補給。終點昂坪市集有商店及餐廳。",
 toilets_en="Pak Kung Au (start) and Ngong Ping (end). None on trail.",toilets_zh="伯公坳（起點）及昂坪（終點）。沿途沒有。",
 exits_en=["At post L020, turn left onto South Lantau Country Trail back to Pak Kung Au"],exits_zh=["於標距柱L020左轉，經南大嶼郊遊徑返回伯公坳"],
 to_start=PKA_IN,from_end=NP_OUT,
 safety_en="Very steep stone steps, ~630 m climb; exposed summit with strong wind, fog, cold in winter. Descent is steep and rocky. Pre-dawn hikers need torches.",
 safety_zh="石級非常陡峭，爬升約630米；山頂當風，多霧，冬季寒冷。落山路段陡峭多石。摸黑上山看日出須帶電筒。",
 sources=[AFCD[3],WIKI,"https://www.oasistrek.com/lantau_trail_three.php",TOI,NLB+"22",NLB+"5","https://www.np360.com.hk/en/visitor-information/tourist-guide"]),
dict(n=4,start_en="Ngong Ping",start_zh="昂坪",end_en="Sham Wat Road",end_zh="深屈道",km=4,hours=1.25,difficulty="Moderate (AFCD 2★)",posts=["L027","L035"],posts_estimated=False,
 highlights_en=["Wisdom Path (Heart Sutra wooden pillars)","Views of Lantau Peak range","Shek Pik Reservoir"],
 highlights_zh=["心經簡林","鳳凰山山脈景色","石壁水塘"],high_point=None,
 water_en="Ngong Ping Village at the start. Nothing after.",water_zh="起點昂坪市集可補給，之後沒有。",
 toilets_en="Ngong Ping (start). None after.",toilets_zh="昂坪（起點）。之後沒有。",
 exits_en=["Near start: back to Ngong Ping bus terminus","Part of the route follows Ngong Ping Road"],exits_zh=["近起點：返回昂坪巴士總站","部分路段沿昂坪路"],
 to_start=NP_BUS_IN,from_end=SW_OUT,
 safety_en="Easy; watch for traffic on road sections. Route was realigned in 2008 after landslides – follow signs.",
 safety_zh="容易；車路段注意車輛。2008年山泥傾瀉後改道，請跟隨路牌。",
 sources=[AFCD[4],WIKI,"https://www.oasistrek.com/lantau_trail_four.php",NLB+"21",NLB+"4",NLB+"19"]),
dict(n=5,start_en="Sham Wat Road",start_zh="深屈道",end_en="Man Cheung Po",end_zh="萬丈布",km=7.5,hours=3,difficulty="Demanding (AFCD 3★)",posts=["L035","L050"],posts_estimated=False,
 highlights_en=["Kwun Yam Temple (1910)","Keung Shan and Ling Wui Shan ridge","Man Cheung Po waterfalls"],
 highlights_zh=["觀音寺（1910年）","羗山及靈會山山脊","萬丈布瀑布"],
 high_point={"name_en":"Ling Wui Shan","name_zh":"靈會山","m":490},
 water_en="None. Seasonal stream at Man Cheung Po campsite (treat before drinking).",water_zh="沒有補給。萬丈布營地有季節性溪水（須處理）。",
 toilets_en="None on trail. Dry pit toilet at Man Cheung Po campsite.",toilets_zh="沿途沒有。萬丈布營地有旱廁。",
 exits_en=["After Keung Shan: branch right to Lung Tsai Ng Yuen","Keung Shan Country Trail down towards Keung Shan / Tai O Road"],exits_zh=["過羗山後右轉支路往龍仔悟園","羗山郊遊徑落羗山道／大澳道"],
 to_start=SW_IN,from_end=LUNG_OUT,
 safety_en="Sustained climbs to Keung Shan/Ling Wui Shan with little shade. Lung Tsai Ng Yuen is private – do not climb on the zig-zag bridge stones.",
 safety_zh="上羗山及靈會山長斜，少遮蔭。龍仔悟園屬私人地方，勿倚坐九曲橋石塊。",
 sources=[AFCD[5],WIKI,"https://www.oasistrek.com/lantau_trail_five.php",CAMP+"34_ManCheungPo.html","https://www.facebook.com/BIGPACK.hk/videos/lantau-trail-5-ling-wui-shan-490m-112021/573477240435333/",NLB+"1"]),
dict(n=6,start_en="Man Cheung Po",start_zh="萬丈布",end_en="Tai O",end_zh="大澳",km=2.5,hours=0.75,difficulty="Moderate (AFCD 2★)",posts=["L050","L055"],posts_estimated=False,
 highlights_en=["Lung Tsai Ng Yuen garden","Panorama of Tai O from Nam Yam Ting pavilion","Old stone path and Nam Chung Village"],
 highlights_zh=["龍仔悟園","南音亭俯瞰大澳","石砌古道及南涌村"],high_point=None,
 water_en="None until Tai O (many shops and restaurants).",water_zh="到大澳才有補給（大量商店及食肆）。",
 toilets_en="Dry pit at Man Cheung Po campsite; public toilets in Tai O.",toilets_zh="萬丈布營地旱廁；大澳有公廁。",
 exits_en=["Near L051: Keung Shan Country Trail / catchwater down to Lung Chai bus stop"],exits_zh=["標距柱L051附近：經羗山郊遊徑／引水道落龍仔巴士站"],
 to_start=LUNG_IN,from_end=TAIO_OUT,
 safety_en="Very steep stone-step descent to Tai O; mossy and slippery when wet. Use handrails.",
 safety_zh="落大澳石級非常陡峭，有青苔，雨天濕滑，請扶欄杆。",
 sources=[AFCD[6],WIKI,"https://www.oasistrek.com/lantau_trail_six.php",NLB+"14"]),
dict(n=7,start_en="Tai O",start_zh="大澳",end_en="Kau Ling Chung",end_zh="狗嶺涌",km=10.5,hours=3.5,difficulty="Demanding (AFCD 3★)",posts=["L055","L076"],posts_estimated=False,
 highlights_en=["Yi O mangroves and farmland","Fan Lau Fort and Pearl River estuary 'two-colour' water","Chicken Wing (Kai Yet Kok) and remote beaches"],
 highlights_zh=["二澳紅樹林及農田","分流炮台及珠江口「鴛鴦水」","雞翼角及偏遠海灘"],high_point=None,
 water_en="Tai O at start. Small store in Fan Lau village (irregular hours). Seasonal streams at campsites.",water_zh="起點大澳補給。分流村有小士多（營業時間不定）。營地有季節性溪水。",
 toilets_en="Tai O (start). Dry pit toilet at Kau Ling Chung campsite.",toilets_zh="大澳（起點）。狗嶺涌營地有旱廁。",
 exits_en=["No road exits – turn back to Tai O, or continue to Kau Ling Chung then ~1 hr catchwater walk to Shek Pik"],exits_zh=["沒有車路出口：折返大澳，或繼續到狗嶺涌再沿引水道步行約1小時到石壁"],
 to_start=TAIO_IN,from_end=SHATSUI("out"),
 safety_en="PART CLOSED until further notice (AFCD): landslides (notice 10 Oct 2025) and private-land farming at Yi O villages – follow site diversions. Fan Lau Country Trail, Kau Ling Chung–Fan Shui Au and Tsin Yue Wan campsite also closed. Remote, no exits; overgrown in places. Allow extra ~1 hr to reach buses.",
 safety_zh="部分路段封閉直至另行通知（漁護署）：山泥傾瀉（2025年10月10日通告）及二澳村私人土地復耕，請按現場改道指示。分流郊遊徑、狗嶺涌至分水坳及煎魚灣營地亦封閉。路段偏遠無出口，部分草叢茂密。到車站須另加約1小時。",
 sources=[AFCD[7],NEWS,"https://www.hiking.gov.hk/console/public/uploads/news/673c30e827639.pdf","https://www.hiking.gov.hk/console/public/uploads/news/67e25fb810da6.pdf",WIKI,"https://www.oasistrek.com/lantau_trail_seven.php",CAMP+"33_KauLingChung.html"]),
dict(n=8,start_en="Kau Ling Chung",start_zh="狗嶺涌",end_en="Shek Pik",end_zh="石壁",km=5.5,hours=2,difficulty="Moderate (AFCD 2★)",posts=["L076","L087"],posts_estimated=False,
 highlights_en=["Lantau South Obelisk (1902)","Views of Soko Islands","Shek Pik Hung Hau Ancient Temple"],
 highlights_zh=["大嶼山南界碑（1902年）","遠眺索罟群島","石壁洪侯古廟"],high_point=None,
 water_en="No shops. Seasonal streams at Kau Ling Chung and Tai Long Wan campsites. Tap at toilets near Shek Pik (Wang Pui Road entrance).",water_zh="沒有商店。狗嶺涌及大浪灣營地有季節性溪水。石壁宏貝道入口附近廁所有水。",
 toilets_en="Dry pits at Kau Ling Chung and Tai Long Wan campsites; flushing toilets near Wang Pui Road entrance, Shek Pik.",toilets_zh="狗嶺涌及大浪灣營地旱廁；石壁宏貝道入口附近有沖水廁所。",
 exits_en=["None mid-stage; the stage ends at the nearest road (Shek Pik)"],exits_zh=["中途沒有出口，終點石壁為最近車路"],
 to_start=[T("bus","NLB 1, 2, 11, 23","Mui Wo (1, 2) / Tung Chung (11, 23)","梅窩（1、2）／東涌（11、23）","No road to Kau Ling Chung: alight at 'Sha Tsui' and walk ~1 hr along the catchwater.","狗嶺涌不通車：於「沙咀」站下車，沿引水道步行約1小時。")],
 from_end=SHATSUI("out"),
 safety_en="Mostly concrete catchwater, easy but long and remote. Carry enough water.",safety_zh="大部分為引水道石屎路，容易但偏遠路長，須帶足水。",
 sources=[AFCD[8],WIKI,"https://www.oasistrek.com/lantau_trail_eight.php",CAMP+"33_KauLingChung.html",CAMP+"32_TaiLongWan.html",CAMP+"39_ShekPik.html"]),
dict(n=9,start_en="Shek Pik",start_zh="石壁",end_en="Shui Hau",end_zh="水口",km=6.5,hours=2,difficulty="Moderate (AFCD 2★)",posts=["L087","L100"],posts_estimated=False,
 highlights_en=["Shek Pik Reservoir dam and viewing platform","Shek Pik rock carving (~3,000 years old)","Shek Lam Chau and Lo Kei Wan beaches"],
 highlights_zh=["石壁水塘主壩及觀景台","石壁石刻（約3000年）","石欖洲及籮箕灣海灘"],high_point=None,
 water_en="None until Shui Hau (village store). Seasonal streams at Shek Lam Chau (L092) and Lo Kei Wan campsites.",water_zh="到水口村才有士多。石欖洲（L092）及籮箕灣營地有季節性溪水。",
 toilets_en="Near Shek Pik (start); dry pits at Shek Lam Chau and Lo Kei Wan campsites.",toilets_zh="石壁附近（起點）；石欖洲及籮箕灣營地有旱廁。",
 exits_en=["No easy exits – continue to Shui Hau or return to Shek Pik"],exits_zh=["沒有方便出口：繼續往水口或折返石壁"],
 to_start=SHATSUI("in"),from_end=SHUIHAU("out"),
 safety_en="Gentle coastal path. Shek Pik Country Trail (links Shek Lam Chau) closed since 24 Jul 2026 – do not use it as a shortcut.",
 safety_zh="平緩海岸路。石壁郊遊徑（連接石欖洲）自2026年7月24日起封閉，切勿取道。",
 sources=[AFCD[9],WIKI,"https://www.oasistrek.com/lantau_trail_nine.php",CAMP+"31_ShekLamChau.html",CAMP+"30_LoKeiWan.html",NEWS,"https://www.trailchallenger.com/lantau-trail-guide"]),
dict(n=10,start_en="Shui Hau",start_zh="水口",end_en="Cheung Sha (post L113, Tung Chung Road)",end_zh="長沙（標距柱L113，東涌道）",km=6.5,hours=2,difficulty="Moderate (AFCD 2★)",posts=["L100","L113"],posts_estimated=False,
 highlights_en=["Shui Hau mudflat (horseshoe crabs at low tide)","Views of Tong Fuk and Cheung Sha beaches","Shaded catchwater walk"],
 highlights_zh=["水口泥灘（潮退可見馬蹄蟹）","俯瞰塘福及長沙海灘","有蔭引水道"],high_point=None,
 water_en="Shui Hau village at start. None on trail; Tong Fuk/Cheung Sha shops need a detour to South Lantau Road.",water_zh="起點水口村可補給。沿途沒有；塘福／長沙商店須繞落嶼南道。",
 toilets_en="None on trail.",toilets_zh="沿途沒有。",
 exits_en=["Vehicle track near Ma Po Ping / Tong Fuk prison down to South Lantau Road","At L113: right, ~20 min down to Cheung Sha Bridge bus stop"],exits_zh=["近麻埔坪／塘福懲教所車路落嶼南道","L113右轉，約20分鐘落長沙大橋巴士站"],
 to_start=SHUIHAU("in"),from_end=CSB("out"),
 safety_en="Uphill start; watch for mountain bikers on shared sections. Stage end is up on the hillside, ~20 min from the bus.",
 safety_zh="起步上斜；共用路段留意越野單車。終點在山腰，距巴士站約20分鐘。",
 sources=[AFCD[10],WIKI,"https://www.oasistrek.com/lantau_trail_ten.php","https://www.trailchallenger.com/lantau-trail-guide",NLB+"1"]),
dict(n=11,start_en="Cheung Sha (post L113, Tung Chung Road)",start_zh="長沙（標距柱L113，東涌道）",end_en="Pui O",end_zh="貝澳",km=4.5,hours=1.25,difficulty="Moderate (AFCD 2★)",posts=["L113","L122"],posts_estimated=False,
 highlights_en=["Shaded woodland with streams","Views of Pui O Bay, Chi Ma Wan and Shek Kwu Chau","Pui O Beach"],
 highlights_zh=["有蔭樹林及小溪","遠眺貝澳灣、芝麻灣及石鼓洲","貝澳泳灘"],high_point=None,
 water_en="None on trail. Shops and cafés at Pui O village and beach.",water_zh="沿途沒有。貝澳村及海灘有商店及餐廳。",
 toilets_en="None on trail; at Pui O Beach (end).",toilets_zh="沿途沒有；終點貝澳泳灘有。",
 exits_en=["Near start: steps up to Tung Chung Road (ask driver for stop)"],exits_zh=["近起點：石級上東涌道（先向司機查詢車站）"],
 to_start=CSB("in"),from_end=LOUK("out"),
 safety_en="Easiest stage. Final stone-step descent to Shui Nam Road/Pui O can be slippery.",safety_zh="最易行的一段。最後落水南路／貝澳的石級或濕滑。",
 sources=[AFCD[11],WIKI,"https://www.oasistrek.com/lantau_trail_eleven.php",NLB+"7"]),
dict(n=12,start_en="Pui O",start_zh="貝澳",end_en="Mui Wo",end_zh="梅窩",km=9,hours=3,difficulty="Demanding (AFCD 3★)",posts=["L122","L140"],posts_estimated=False,
 highlights_en=["Feral water buffalo at Pui O","Views of Pui O Wan and Chi Ma Wan","Silver Mine Bay and old mining area"],
 highlights_zh=["貝澳野水牛","貝澳灣及芝麻灣景色","銀礦灣及舊礦場"],high_point=None,
 water_en="Pui O at start. Seasonal stream at Pak Fu Tin campsite (L132). Shops and restaurants in Mui Wo.",water_zh="起點貝澳補給。白富田營地（L132）有季節性溪水。梅窩有商店及食肆。",
 toilets_en="Pui O (start); dry pit at Pak Fu Tin campsite; Mui Wo Ferry Pier (end).",toilets_zh="貝澳（起點）；白富田營地旱廁；梅窩碼頭（終點）。",
 exits_en=["At L130: turn left on side path to South Lantau Road","After Pak Fu Tin, on reaching the road turn left to South Lantau Road"],exits_zh=["標距柱L130左轉支路往嶼南道","過白富田接上馬路後左轉往嶼南道"],
 to_start=LOUK("in"),from_end=[FERRY_OUT,B3M_OUT,TAXI_MW],
 safety_en="Several climbs in forest. A section of the Mui Wo–Pui O Mountain Bike Trail is closed (since 30 Jun 2026) – follow on-site signs.",
 safety_zh="林中有數段上斜。梅窩至貝澳越野單車徑部分路段自2026年6月30日起封閉，請留意現場指示。",
 sources=[AFCD[12],WIKI,"https://www.oasistrek.com/lantau_trail_twelve.php",CAMP+"28_PakFuTin.html",NEWS,"https://www.sunferry.com.hk/en/route-and-fare/timetable?route=central-to-mui-wo"]),
]
for s in stages:
    s["sources"].append("https://www.oasistrek.com/lantau_trail.php") if False else None
trail={"id":"lantau","name_en":"Lantau Trail","name_zh":"鳳凰徑","total_km":70,"post_prefix":"L",
 "notes":"70 km loop from Mui Wo, 12 stages, mostly in Lantau South/North Country Parks. Distance posts every 500 m, L001 near Mui Wo to L140 back at Mui Wo (some guides call the start L000). Give your post number when calling 999. Stages 2–3 (Sunset Peak 869 m, Lantau Peak 934 m) are the hardest and most exposed. Part of Stage 7 (Yi O / Fan Lau area) is closed until further notice – check hiking.gov.hk before going. AFCD difficulty: 1★ Easy, 2★ Moderate, 3★ Demanding, 4★ Difficult. All buses are New Lantao Bus (NLB); routes 2, 4 and 21 are sparse – check nlb.com.hk timetables.",
 "notes_zh":"由梅窩出發的70公里環迴路線，共12段，主要位於南、北大嶼郊野公園。每500米一枝標距柱，由梅窩附近L001至返回梅窩的L140（部分指南稱起點為L000）。致電999求救時請報標距柱編號。第二、三段（大東山869米、鳳凰山934米）最辛苦及當風。第七段部分路段（二澳／分流一帶）封閉直至另行通知，出發前請查閱郊野樂行網站。漁護署難度：1星易行、2星普通、3星費力、4星難行。所有巴士為新大嶼山巴士；2、4及21號班次疏，請查閱時間表。"}
out={"trail":trail,"stages":stages}
p="/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/research/lantau.json"
json.dump(out,open(p,"w"),ensure_ascii=False,indent=1)
# sanity
print(sum(s["km"] for s in stages), [s["posts"] for s in stages])
