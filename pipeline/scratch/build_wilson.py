import json
AFCD = {
 1:"https://www.hiking.gov.hk/trail/info/id/TCtocVVTL1JuMXpaQVBSOFBYYzRSUT09",
 2:"https://www.hiking.gov.hk/trail/info/id/cktQWGdYRkF1MEsvNXFHQVk2Sm5FQT09",
 3:"https://www.hiking.gov.hk/trail/info/id/Z05QUVAxMnphOXBCSGlwSkhKVE1Zdz09",
 4:"https://www.hiking.gov.hk/trail/info/id/Q3hxOUd0N3FPcVZMeXdBZi93U0t0dz09",
 5:"https://www.hiking.gov.hk/trail/info/id/Sk1oNnZ1NlE3VksxUU1CekZYYkZuUT09",
 6:"https://www.hiking.gov.hk/trail/info/id/M3ArN2RxYmROLzBKNlhxRndlRUdzZz09",
 7:"https://www.hiking.gov.hk/trail/info/id/anRlQ0Q2VTA5SUhNQjBTSm9tRGJhUT09",
 8:"https://www.hiking.gov.hk/trail/info/id/dGljejY4cWNjZ3E5Z2wwK1V3cWtJZz09",
 9:"https://www.hiking.gov.hk/trail/info/id/TjFJNDlpb0FhSmdCS25nYTg5K0pmQT09",
 10:"https://www.hiking.gov.hk/trail/info/id/azJKaHRIeUFIbXZWN0UyVU1ZS1hFdz09",
}
OASIS = {1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten"}
WIKI = "https://en.wikipedia.org/wiki/Wilson_Trail"
POSTS_PDF = "https://www.afcd.gov.hk/english/country/cou_wha/files/distance_post_wilson_trail_20141031.pdf"

def T(mode, route, from_en, from_zh, note_en="", note_zh=""):
    d = {"mode": mode, "route": route, "from_en": from_en, "from_zh": from_zh}
    if note_en: d["note_en"] = note_en
    if note_zh: d["note_zh"] = note_zh
    return d

stages = []

# ---------- Stage 1
stages.append({
 "n":1,"start_en":"Stanley Gap Road","start_zh":"赤柱峽道",
 "end_en":"Wong Nai Chung Reservoir (Wong Nai Chung Gap)","end_zh":"黃泥涌水塘（黃泥涌峽）",
 "km":4.8,"hours":2.75,"difficulty":"4/5 Difficult (AFCD)","difficulty_zh":"4星 難行（漁護署）",
 "posts":["W001","W008"],"posts_estimated":False,
 "highlights_en":["The Twins: 1,000+ stone steps over South & North peaks","Views of Stanley, Tai Tam and Po Toi","Chinese New Year flowers on Violet Hill"],
 "highlights_zh":["孖崗山過千級石階，南崗、北崗","遠眺赤柱、大潭及蒲台島","紫羅蘭山農曆新年吊鐘花"],
 "high_point":{"name_en":"Violet Hill upper slopes (Twins South Peak 386 m)","name_zh":"紫羅蘭山山腰（孖崗山南崗386米）","m":420,"m_note":"~420 m is a GPS max (TimHiking); named summit on route: Twins South Peak 386 m (AFCD)"},
 "water_en":"None on trail. Snack kiosk at Wong Nai Chung Reservoir at the end.",
 "water_zh":"沿途無補給；終點黃泥涌水塘有小食亭。",
 "toilets_en":"None on trail; toilets at Wong Nai Chung Reservoir Park (end).",
 "toilets_zh":"沿途無廁所；終點黃泥涌水塘公園有廁所。",
 "exits_en":["Repulse Bay Gap: take level Violet Hill Path to Wong Nai Chung Reservoir, skipping Violet Hill climb"],
 "exits_zh":["淺水灣坳：經紫羅蘭山徑往黃泥涌水塘，避開紫羅蘭山爬升"],
 "to_start":[
   T("bus","Citybus 6A","Central (Exchange Square)","中環（交易廣場）","Towards Stanley Fort; alight 'Wilson Trail' stop, Stanley Gap Rd","往赤柱炮台，於赤柱峽道「衞奕信徑」站下車"),
   T("bus","Citybus 260","Central (Exchange Square)","中環（交易廣場）","Express via Aberdeen Tunnel; alight 'Wilson Trail' stop","經香港仔隧道；「衞奕信徑」站下車"),
   T("bus","Citybus 73","Cyberport / Wah Fu / Aberdeen","數碼港／華富／香港仔","Via Repulse Bay; alight 'Wilson Trail' stop","經淺水灣；「衞奕信徑」站下車"),
   T("taxi","","Anywhere","任何地點","Ask for Wilson Trail, Stanley Gap Road","告知往赤柱峽道衞奕信徑入口")],
 "from_end":[
   T("bus","Citybus 6","Wong Nai Chung Reservoir Park / Tai Tam Reservoir Rd stop","黃泥涌水塘公園／大潭水塘道站","To Central","往中環"),
   T("bus","Citybus 41A, 63","Wong Nai Chung Gap Road","黃泥涌峽道","To North Point","往北角"),
   T("bus","Citybus 76","Wong Nai Chung Gap Road","黃泥涌峽道","To Causeway Bay","往銅鑼灣"),
   T("bus","Citybus 1M","Wong Nai Chung Gap Road","黃泥涌峽道","To Exhibition Centre MTR (circular)","往會展站（循環線）"),
   T("bus","Citybus A17","Wong Nai Chung Gap Road","黃泥涌峽道","Airport bus","往機場"),
   T("gmb","5","Tai Tam Reservoir Road","大潭水塘道","HK Island GMB: Causeway Bay (Sogo) / Aberdeen","港島專線小巴：往銅鑼灣或香港仔"),
   T("taxi","","Wong Nai Chung Gap Road","黃泥涌峽道","","")],
 "safety_en":"Very steep, relentless steps up and down the Twins; little shade, no water on trail — carry plenty.",
 "safety_zh":"孖崗山梯級極陡、急上急落；樹蔭少、沿途無補給，須帶足水。",
 "sources":[AFCD[1],"https://www.oasistrek.com/wilson_trail_one.php","https://www.hkallshan.com/wilson-trail-section-1/","https://timhiking.com/en/blog.php?d=190711","https://mytrail.run/blogs/post/the-wilson-trail-section-1","https://rt.data.gov.hk/v2/transport/citybus/route-stop/CTB/260/outbound",WIKI]
})

# ---------- Stage 2
stages.append({
 "n":2,"start_en":"Wong Nai Chung Reservoir (Parkview)","start_zh":"黃泥涌水塘（陽明山莊）",
 "end_en":"Quarry Bay (MTR Tai Koo); official end Lam Tin via MTR","end_zh":"鰂魚涌（港鐵太古站）；正式終點為藍田站",
 "km":6.6,"hours":2.5,"difficulty":"3/5 Demanding (AFCD)","difficulty_zh":"3星 費力（漁護署）",
 "posts":["W009","W018"],"posts_estimated":False,
 "highlights_en":["Jardine's Lookout viewpoint over Victoria Harbour","WWII relics: Osborn Memorial, wartime stoves, Japanese tunnel","Mount Butler Quarry and Quarry Bay Tree Walk"],
 "highlights_zh":["渣甸山觀景台俯瞰維港","二戰遺跡：奧斯本紀念碑、戰時爐灶、日軍地道","畢拿山石礦場及鰂魚涌樹木研習徑"],
 "high_point":{"name_en":"Jardine's Lookout","name_zh":"渣甸山","m":433},
 "water_en":"Shop at Parkview near start; none on trail; shops in Quarry Bay/Tai Koo at end.",
 "water_zh":"起點陽明山莊有超市；沿途無補給；終點鰂魚涌／太古有商店。",
 "toilets_en":"Wong Nai Chung Reservoir Park (start); urban toilets at Quarry Bay/Tai Koo.",
 "toilets_zh":"起點黃泥涌水塘公園；終點鰂魚涌／太古市區。",
 "exits_en":["Mount Parker Road down to King's Road, Quarry Bay","Jardine's Lookout North Catchwater (check map)"],
 "exits_zh":["柏架山道落英皇道（鰂魚涌）","渣甸山北引水道（請查地圖）"],
 "to_start":[
   T("bus","Citybus 6","Central (Exchange Square)","中環（交易廣場）","Alight Wong Nai Chung Reservoir Park; walk up Tai Tam Reservoir Rd","黃泥涌水塘公園下車，沿大潭水塘道上行"),
   T("bus","Citybus 41A, 63","North Point","北角","Alight Wong Nai Chung Gap Road","黃泥涌峽道下車"),
   T("bus","Citybus 76, 1M, A17","Causeway Bay / Exhibition Centre / Airport","銅鑼灣／會展／機場",""," "),
   T("gmb","5","Causeway Bay (Sogo)","銅鑼灣（崇光）","Alight Tai Tam Reservoir Road","大潭水塘道下車")],
 "from_end":[
   T("mtr","Island Line","Tai Koo","太古","From W018 walk Greig Rd & King's Rd (~2 min from Greig Rd) to Tai Koo","於W018右轉，經基利路及英皇道往太古站"),
   T("mtr","Island Line + Tseung Kwan O Line","Tai Koo → Quarry Bay → Yau Tong","太古→鰂魚涌→油塘","HARBOUR CROSSING to Stage 3: change at Quarry Bay to TKO Line, alight Yau Tong (Exit A1)","過海往第三段：鰂魚涌轉將軍澳綫，油塘站A1出口"),
   T("mtr","Kwun Tong Line","Yau Tong → Lam Tin","油塘→藍田","Official route ends at Lam Tin Exit A (change at Yau Tong)","正式終點藍田站A出口（油塘轉車）"),
   T("bus","Various","King's Road, Quarry Bay","鰂魚涌英皇道","Buses/trams along King's Road for early exit","英皇道有巴士、電車")],
 "safety_en":"Marble-type steps slippery when wet; many junctions in later part — carry offline map.",
 "safety_zh":"部分石級潮濕時易滑；後段分岔多，宜帶離線地圖。",
 "sources":[AFCD[2],"https://www.oasistrek.com/wilson_trail_two.php","https://www.hkallshan.com/wilson-trail-section2/","https://mytrail.run/blogs/post/the-wilson-trail-section-2",WIKI]
})

# ---------- Stage 3
stages.append({
 "n":3,"start_en":"Lam Tin (or Yau Tong)","start_zh":"藍田（或油塘）",
 "end_en":"Tseng Lan Shue","end_zh":"井欄樹",
 "km":9.3,"hours":3.5,"difficulty":"4/5 Difficult (AFCD)","difficulty_zh":"4星 難行（漁護署）",
 "posts":["W019","W031"],"posts_estimated":False,
 "highlights_en":["Devil's Peak military relics, Gough Battery","Black Hill views over Tseung Kwan O","Rural villages: Ma Yau Tong, Au Tau"],
 "highlights_zh":["魔鬼山軍事遺跡、歌賦砲台","五桂山俯瞰將軍澳","馬游塘、凹頭田園風光"],
 "high_point":{"name_en":"Black Hill","name_zh":"五桂山","m":304},
 "water_en":"Drinks vending machine at Ma Yau Tong; store/vending at Tseng Lan Shue (end).",
 "water_zh":"馬游塘有汽水機；終點井欄樹有士多／汽水機。",
 "toilets_en":"Domain mall, Yau Tong (start); Tseng Lan Shue (end).",
 "toilets_zh":"油塘大本型商場（起點）；井欄樹（終點）。",
 "exits_en":["O King Road (cemetery road) down to Yau Tong","Black Hill: path down to Lam Tin Park","Po Lam Road"],
 "exits_zh":["澳景路落油塘","五桂山落藍田公園","寶琳路"],
 "to_start":[
   T("mtr","Tseung Kwan O Line","Yau Tong Exit A1","油塘站A1出口","Walk Cha Kwo Ling Rd & Ko Chiu Rd ~1 km to W019 (shortest)","經茶果嶺道、高超道步行約1公里至W019"),
   T("mtr","Kwun Tong Line","Lam Tin Exit A","藍田站A出口","Official start; ~2 km via Kai Tin, Lei Yue Mun & Ko Chiu Rds to W019","正式起點；經啟田道、鯉魚門道、高超道約2公里至W019")],
 "from_end":[
   T("bus","KMB 91, 91M, 92","Tseng Lan Shue stop, Clear Water Bay Rd","清水灣道「井欄樹」站","To Diamond Hill MTR","往鑽石山站"),
   T("bus","KMB 91P, 92R, 96R","Tseng Lan Shue stop","「井欄樹」站","Special/holiday routes","特別／假日路線"),
   T("gmb","1, 1A, 11","Tseng Lan Shue","井欄樹","Via Choi Hung MTR","經彩虹站"),
   T("gmb","12, 104, 11B","Tseng Lan Shue","井欄樹","Listed by AFCD; check destination","漁護署列出；請查目的地"),
   T("rmb","Kwun Tong / Mong Kok","Clear Water Bay Road","清水灣道","Red minibuses Sai Kung–Kwun Tong and Sai Kung–Mong Kok","西貢往觀塘／旺角紅van")],
 "safety_en":"Little shade; several road crossings; signage patchy through villages.",
 "safety_zh":"樹蔭少；須橫過馬路；村落段路牌不足。",
 "sources":[AFCD[3],"https://www.oasistrek.com/wilson_trail_three.php","https://www.hkallshan.com/wilson-trail-section-3/","https://mytrail.run/blogs/post/the-wilson-trail-section-3","https://en.wikipedia.org/wiki/Black_Hill,_Hong_Kong","https://data.etabus.gov.hk/v1/transport/kmb/route/","https://www.16seats.net/eng/gmb/gn_1a.html"]
})

# ---------- Stage 4
stages.append({
 "n":4,"start_en":"Tseng Lan Shue","start_zh":"井欄樹",
 "end_en":"Sha Tin Pass","end_zh":"沙田坳",
 "km":8.0,"hours":3.5,"difficulty":"4/5 Difficult (AFCD)","difficulty_zh":"4星 難行（漁護署）",
 "posts":["W032","W046"],"posts_estimated":False,
 "highlights_en":["Shaded ancient stone trail to Tai Lam Wu","Tung Yeung Shan silvergrass (autumn/winter)","Kowloon Peak viewpoints; Lover's Rock at Sha Tin Pass"],
 "highlights_zh":["林蔭古道往大藍湖","東洋山秋冬芒草","飛鵝山觀景台；沙田坳姻緣石"],
 "high_point":{"name_en":"Tung Yeung Shan","name_zh":"東洋山","m":533},
 "water_en":"Stores at Tseng Lan Shue (start) and Sha Tin Pass (Hang Yik store, cup noodles).",
 "water_zh":"井欄樹及沙田坳（恒益商店，有杯麵）有士多。",
 "toilets_en":"Tseng Lan Shue, Kowloon Peak viewpoint (Fei Ngo Shan Road), Sha Tin Pass.",
 "toilets_zh":"井欄樹、飛鵝山觀景台、沙田坳。",
 "exits_en":["Tai Lam Wu down to Ho Chung","Fei Ngo Shan Road down to Clear Water Bay Road"],
 "exits_zh":["大藍湖落蠔涌","飛鵝山道接清水灣道"],
 "to_start":[
   T("bus","KMB 91, 91M, 92","Diamond Hill MTR (91M also Po Lam)","鑽石山站（91M亦由寶林）","Alight Tseng Lan Shue; 5 min walk","井欄樹站下車，步行5分鐘"),
   T("gmb","11","Choi Hung MTR","彩虹站","Alight Tseng Lan Shue","井欄樹下車"),
   T("gmb","1, 1A","Choi Hung MTR","彩虹站","Towards Sai Kung; alight Tseng Lan Shue","往西貢，井欄樹下車"),
   T("rmb","Mong Kok / Kwun Tong – Sai Kung","Mong Kok (Dundas St) / Kwun Tong","旺角（登打士街）／觀塘","Alight Tseng Lan Shue","井欄樹下車")],
 "from_end":[
   T("bus","KMB 2F, 3C, 3M, 15A","Tsz Wan Shan (North) terminus","慈雲山（北）總站","Walk down steps from Sha Tin Pass (~25 min)","由沙田坳沿石級下山約25分鐘"),
   T("bus","Citybus A23","Tsz Wan Shan (North) terminus","慈雲山（北）總站","Airport bus","往機場"),
   T("gmb","19, 19M, 37A, 73","Tsz Wan Shan (North)","慈雲山（北）","37A to Wong Tai Sin MTR","37A往黃大仙站")],
 "safety_en":"Steep, loose descent off Tung Yeung Shan; long exposed climb with little shade.",
 "safety_zh":"東洋山下山路段陡峭、碎石鬆散；爬升長而少樹蔭。",
 "sources":[AFCD[4],"https://www.oasistrek.com/wilson_trail_four.php","https://www.hkallshan.com/wilson-trail-section4/","https://mytrail.run/blogs/post/the-wilson-trail-section-4","https://peakvisor.com/peak/tung-yeung-shan.html","https://data.etabus.gov.hk/v1/transport/kmb/route/","https://www.16seats.net/eng/gmb/gk_37a.html"]
})

# ---------- Stage 5
stages.append({
 "n":5,"start_en":"Sha Tin Pass","start_zh":"沙田坳",
 "end_en":"Tai Po Road (Kowloon Reservoir)","end_zh":"大埔公路（九龍水塘）",
 "km":7.4,"hours":2.25,"difficulty":"2/5 Moderate (AFCD)","difficulty_zh":"2星 普通（漁護署）",
 "posts":["W047","W060"],"posts_estimated":False,
 "highlights_en":["Amah Rock","Catchwater views of Sha Tin, Tai Wai, Tolo Harbour","Kowloon Reservoir Record Instrument House (monument)"],
 "highlights_zh":["望夫石","引水道遠眺沙田、大圍、吐露港","九龍水塘記錄儀器房（法定古蹟）"],
 "water_en":"Hang Yik store at Sha Tin Pass (start); none on trail.",
 "water_zh":"起點沙田坳恒益士多；沿途無補給。",
 "toilets_en":"Sha Tin Pass (start).",
 "toilets_zh":"沙田坳（起點）。",
 "exits_en":["Hung Mui Kuk down to Tai Wai"],
 "exits_zh":["紅梅谷落大圍"],
 "to_start":[
   T("bus","KMB 2F, 3C, 3M, 15A; Citybus A23","Various, to Tsz Wan Shan (North) terminus","慈雲山（北）總站","Then ~25 min uphill on steps to Sha Tin Pass","再沿石級上山約25分鐘"),
   T("gmb","19, 19M, 37A, 73","To Tsz Wan Shan (North); 37A from Wong Tai Sin MTR","往慈雲山（北）；37A由黃大仙站","Then ~25 min uphill","再上山約25分鐘"),
   T("gmb","18M","Wong Tai Sin MTR","黃大仙站","Alight Fat Jong Temple, walk Sha Tin Pass Road (40–60 min)","法藏寺下車，經沙田坳道步行40–60分鐘")],
 "from_end":[
   T("bus","KMB 72","Kowloon Reservoir stop, Tai Po Road","大埔公路「九龍水塘」站","Tai Wo ↔ Cheung Sha Wan","太和↔長沙灣"),
   T("bus","KMB 81","Kowloon Reservoir stop, Tai Po Road","大埔公路「九龍水塘」站","Wo Che ↔ West Kowloon Station","禾輋↔高鐵西九龍站")],
 "safety_en":"Many macaques — don't feed or show food (fine up to HK$10,000); some catchwater edges lack railings.",
 "safety_zh":"獼猴眾多，切勿餵飼或展示食物（最高罰款一萬元）；部分引水道無欄杆。",
 "sources":[AFCD[5],"https://www.oasistrek.com/wilson_trail_five.php","https://www.hkallshan.com/wilson-trail-section5-2/","https://mytrail.run/blogs/post/the-wilson-trail-section-5","https://www.16seats.net/eng/gmb/gk_18m.html","https://data.etabus.gov.hk/v1/transport/kmb/route/"]
})

# ---------- Stage 6
stages.append({
 "n":6,"start_en":"Tai Po Road (Kowloon Reservoir)","start_zh":"大埔公路（九龍水塘）",
 "end_en":"Shing Mun Reservoir (Pineapple Dam)","end_zh":"城門水塘（菠蘿壩）",
 "km":5.3,"hours":2.0,"difficulty":"2/5 Moderate (AFCD)","difficulty_zh":"2星 普通（漁護署）",
 "posts":["W061","W069"],"posts_estimated":False,
 "highlights_en":["Kowloon Reservoir historic dam and valve house","Golden Hill macaques","Shing Mun Reservoir main dam and bellmouth overflow"],
 "highlights_zh":["九龍水塘主壩及水掣房古蹟","金山獼猴","城門水塘主壩及鐘形溢流口"],
 "high_point":{"name_en":"Smugglers' Ridge area","name_zh":"走私坳一帶"},
 "water_en":"Vending machines near Golden Hill Road and Shing Mun Reservoir; kiosk at Pineapple Dam.",
 "water_zh":"金山路及城門水塘附近有汽水機；菠蘿壩有士多。",
 "toilets_en":"Golden Hill Road; Shing Mun Reservoir.",
 "toilets_zh":"金山路；城門水塘。",
 "exits_en":["Golden Hill Road down to Tai Po Road"],
 "exits_zh":["金山路落大埔公路"],
 "to_start":[
   T("bus","KMB 72, 81","Cheung Sha Wan / Sham Shui Po / Sha Tin","長沙灣／深水埗／沙田","Alight 'Kowloon Reservoir' stop; trailhead beside stop","「九龍水塘」站下車，起點在旁")],
 "from_end":[
   T("gmb","82","Pineapple Dam terminus, Shing Mun Reservoir","城門水塘菠蘿壩總站","To Tsuen Wan (Shiu Wo St), near MTR Tsuen Wan","往荃灣兆和街（近荃灣站）"),
   T("bus","KMB 32, 36, 40X, 46X, 47X, 48X, 73X, 278X and others","Ho Fung College stop, Wo Yi Hop Rd","和宜合道「可風中學」站","~20 min walk down Shing Mun Road","沿城門道步行約20分鐘"),
   T("gmb","94, 312, 403, 403A, 403X (94S Sun/PH)","Ho Fung College stop","「可風中學」站","~20 min walk down","步行約20分鐘")],
 "safety_en":"Macaques common — don't feed, hide food and plastic bags. Mostly shaded.",
 "safety_zh":"獼猴常見，切勿餵飼，收好食物及膠袋。大部分有樹蔭。",
 "sources":[AFCD[6],"https://www.oasistrek.com/wilson_trail_six.php","https://www.hkallshan.com/wilson-trail-section6/","https://www.16seats.net/eng/gmb/gn_82.html",WIKI]
})

# ---------- Stage 7
stages.append({
 "n":7,"start_en":"Shing Mun Reservoir (Pineapple Dam)","start_zh":"城門水塘（菠蘿壩）",
 "end_en":"Yuen Tun Ha","end_zh":"元墩下",
 "km":10.2,"hours":3.25,"difficulty":"3/5 Demanding (AFCD)","difficulty_zh":"3星 費力（漁護署）",
 "posts":["W070","W088"],"posts_estimated":False,
 "highlights_en":["Paper-bark tree reflections on Shing Mun Reservoir","Pun Han Pavilion","Lead Mine Pass: junction with MacLehose Trail"],
 "highlights_zh":["城門水塘白千層倒影","半閒亭","鉛鑛坳：與麥理浩徑交匯"],
 "high_point":{"name_en":"Lead Mine Pass","name_zh":"鉛鑛坳"},
 "water_en":"Kiosk/vending at Shing Mun Reservoir; paid water dispenser at Lead Mine Pass; store at Yuen Tun Ha.",
 "water_zh":"城門水塘士多／汽水機；鉛鑛坳付費斟水機；元墩下士多。",
 "toilets_en":"Shing Mun Reservoir picnic/BBQ area; Lead Mine Pass.",
 "toilets_zh":"城門水塘燒烤區；鉛鑛坳。",
 "exits_en":["Backtrack to Pineapple Dam (no other easy exit before Lead Mine Pass)"],
 "exits_zh":["折返菠蘿壩（鉛鑛坳前無其他易行出口）"],
 "to_start":[
   T("gmb","82","Tsuen Wan (Shiu Wo St), near MTR Tsuen Wan","荃灣兆和街（近荃灣站）","To Pineapple Dam terminus","往菠蘿壩總站"),
   T("bus","KMB/GMB via Wo Yi Hop Rd","Various","多條路線","Alight Ho Fung College, walk ~20 min up Shing Mun Road","可風中學下車，沿城門道上行約20分鐘")],
 "from_end":[
   T("gmb","23K","San Uk Ka (walk down from Yuen Tun Ha rain shelter)","新屋家（由元墩下避雨亭下山）","To Tai Po Market MTR, ~10 min ride","往大埔墟站，約10分鐘")],
 "safety_en":"Monkeys at Lead Mine Pass; cattle; many village dogs near Yuen Tun Ha — go in company.",
 "safety_zh":"鉛鑛坳有猴子及牛隻；元墩下一帶村狗多，宜結伴。",
 "sources":[AFCD[7],"https://www.oasistrek.com/wilson_trail_seven.php","https://www.hkallshan.com/wilson-trail-section7/","https://www.16seats.net/eng/gmb/gn_23k.html","https://en.wikipedia.org/wiki/Lead_Mine_Pass"]
})

# ---------- Stage 8
stages.append({
 "n":8,"start_en":"Yuen Tun Ha (San Uk Ka)","start_zh":"元墩下（新屋家）",
 "end_en":"Cloudy Hill summit","end_zh":"九龍坑山山頂",
 "km":9.0,"hours":3.75,"difficulty":"4/5 Difficult (AFCD)","difficulty_zh":"4星 難行（漁護署）",
 "posts":["W089","W105"],"posts_estimated":False,
 "highlights_en":["Wun Yiu kiln site and Fan Sin Temple","King Law Ka Shuk, Tai Po Tau","Cloudy Hill 'sky ladder' with 5 pavilions"],
 "highlights_zh":["碗窰古窰遺址、樊仙宮","大埔頭敬羅家塾","九龍坑山天梯及5個涼亭"],
 "high_point":{"name_en":"Cloudy Hill","name_zh":"九龍坑山","m":440},
 "water_en":"Stores at Yuen Tun Ha, Kam Shek New Village, Tai Po Tau; Tai Wo Plaza. None on Cloudy Hill.",
 "water_zh":"元墩下、錦石新村、大埔頭村士多；太和廣場。九龍坑山上無補給。",
 "toilets_en":"Shek Kwu Lung; Tai Po Tau Village.",
 "toilets_zh":"石古壟；大埔頭村。",
 "exits_en":["Kam Wo Bridge: walk to MTR Tai Wo (last easy exit before the climb)"],
 "exits_zh":["錦和橋步行往港鐵太和站（登山前最後易行出口）"],
 "to_start":[
   T("gmb","23K","Tai Po Market MTR","大埔墟站","To San Uk Ka, ~10 min","往新屋家，約10分鐘"),
   T("mtr","East Rail Line","Tai Wo Exit A","太和站A出口","Joins mid-stage at Kam Wo Bridge (Cloudy Hill part only)","於錦和橋中途加入（只行九龍坑山段）")],
 "from_end":[
   T("gmb","52B","Hok Tau (via Stage 9 down to Hok Tau Reservoir, turn left, walk ~1 km road)","鶴藪（經第九段落鶴藪水塘，左轉沿馬路約1公里）","To Fanling MTR; no transport at summit","往粉嶺站；山頂無交通")],
 "safety_en":"2,000+ steps to Cloudy Hill with little shade; faded signs, easy to go wrong; no transport at the end.",
 "safety_zh":"九龍坑山逾2000級樓梯、少樹蔭；路牌褪色易行錯；終點無交通。",
 "sources":[AFCD[8],"https://www.oasistrek.com/wilson_trail_eight.php","https://www.hkallshan.com/wilson-trail-section8/","https://en.wikipedia.org/wiki/Cloudy_Hill","https://www.16seats.net/eng/gmb/gn_52b.html"]
})

# ---------- Stage 9
stages.append({
 "n":9,"start_en":"Cloudy Hill","start_zh":"九龍坑山",
 "end_en":"Pat Sin Leng (Hsien Ku Fung)","end_zh":"八仙嶺（仙姑峰）",
 "km":10.6,"hours":4.25,"difficulty":"4/5 Difficult (AFCD)","difficulty_zh":"4星 難行（漁護署）",
 "posts":["W106","W125"],"posts_estimated":False,
 "highlights_en":["Hok Tau Reservoir","Ping Fung Shan cliffs and Wong Leng, trail's highest point","Eight peaks of Pat Sin Leng over Plover Cove"],
 "highlights_zh":["鶴藪水塘","屏風山峭壁及全徑最高點黃嶺","八仙嶺八峰俯瞰船灣淡水湖"],
 "high_point":{"name_en":"Wong Leng","name_zh":"黃嶺","m":639},
 "water_en":"None on the ridge; streams near Hok Tau before the climb. Shops at Tai Mei Tuk after descent.",
 "water_zh":"山脊無水源；鶴藪一帶有溪水。下山後大美督有商店。",
 "toilets_en":"Portable toilets at Hok Tau Reservoir; Tai Mei Tuk after descent.",
 "toilets_zh":"鶴藪水塘流動廁所；下山後大美督。",
 "exits_en":["Hok Tau Reservoir (GMB 52B)","Sha Lo Tung","Before Lai Pek Shan at W121: turn right to Wang Tsat Ancient Trail"],
 "exits_zh":["鶴藪水塘（52B小巴）","沙螺洞","犁壁山前W121右轉往橫七古道"],
 "to_start":[
   T("gmb","52B","Fanling MTR (Exit C)","粉嶺站（C出口）","To Hok Tau; most hikers start at Hok Tau Reservoir as Cloudy Hill has no transport","往鶴藪；九龍坑山無交通，多由鶴藪水塘起步")],
 "from_end":[
   T("bus","KMB 75K","Tai Mei Tuk bus terminus","大美督巴士總站","Descend Pat Sin Leng Nature Trail (~40 min); to Tai Po Market MTR","沿八仙嶺自然教育徑下山約40分鐘；往大埔墟站"),
   T("bus","KMB 275R","Tai Mei Tuk bus terminus","大美督巴士總站","Sundays & public holidays only; to Tai Po Market","只限星期日及公眾假期；往大埔墟"),
   T("gmb","20C","Tai Mei Tuk GMB terminus","大美督小巴總站","To Tai Po Market MTR","往大埔墟站")],
 "safety_en":"Exposed ridge, no shade or water — start before 9am, avoid hot days; hill fire risk in dry season (fatal fire 1996).",
 "safety_zh":"山脊外露、無遮蔭無水源，宜9時前起步，避開炎熱天氣；乾燥季節慎防山火（1996年曾釀死亡事故）。",
 "sources":[AFCD[9],"https://www.oasistrek.com/wilson_trail_nine.php","https://www.hkallshan.com/wilson-trail-section9-rea/","https://en.wikipedia.org/wiki/Wong_Leng","https://en.wikipedia.org/wiki/Pat_Sin_Leng","https://www.16seats.net/eng/gmb/gn_20c.html","https://data.etabus.gov.hk/v1/transport/kmb/route/"]
})

# ---------- Stage 10
stages.append({
 "n":10,"start_en":"Pat Sin Leng (Hsien Ku Fung)","start_zh":"八仙嶺（仙姑峰）",
 "end_en":"Nam Chung","end_zh":"南涌",
 "km":6.8,"hours":2.0,"difficulty":"3/5 Demanding (AFCD)","difficulty_zh":"3星 費力（漁護署）",
 "posts":["W126","W137"],"posts_estimated":False,
 "highlights_en":["Wang Tsat Ancient Trail and abandoned Wang Shan Keuk villages","Sir Edward Youde Memorial Pavilion","Starling Inlet, Nam Chung fish ponds and mangroves"],
 "highlights_zh":["橫七古道及荒廢橫山腳村","尤德爵士紀念亭","沙頭角海、南涌魚塘及紅樹林"],
 "high_point":{"name_en":"Hsien Ku Fung (start)","name_zh":"仙姑峰（起點）","m":511},
 "water_en":"None on trail; stores around Luk Keng after the end.",
 "water_zh":"沿途無補給；終點後鹿頸一帶有士多。",
 "toilets_en":"Near Sir Edward Youde Pavilion and Nam Chung pavilion.",
 "toilets_zh":"尤德亭及南涌亭附近。",
 "exits_en":["Wang Shan Keuk junction: path to Wu Kau Tang","Youde Pavilion: path down to Luk Keng"],
 "exits_zh":["橫山腳路口：往烏蛟騰","尤德亭：落鹿頸"],
 "to_start":[
   T("bus","KMB 75K","Tai Po Market MTR","大埔墟站","To Tai Mei Tuk, then ~2 km trail up to junction below Hsien Ku Fung","往大美督，再上山徑約2公里"),
   T("bus","KMB 275R","Tai Po Market MTR","大埔墟站","Sundays & public holidays only","只限星期日及公眾假期"),
   T("gmb","20C, 20R","Tai Po Market MTR","大埔墟站","To Tai Mei Tuk (20R hourly)","往大美督（20R每小時一班）")],
 "from_end":[
   T("gmb","56K","Nam Chung road junction, Luk Keng Road","鹿頸路南涌路口","To Fanling MTR, ~30 min; weekdays every 30 min, ends early evening — check last trip","往粉嶺站約30分鐘；平日30分鐘一班，傍晚收車，請查尾班"),
   T("bus","KMB 78K","'Nam Chung' stop, Sha Tau Kok Road","沙頭角公路「南涌」站","~20–30 min walk out; to Sheung Shui","步行約20–30分鐘；往上水"),
   T("taxi","","Luk Keng Road","鹿頸路","Green NT taxi; may need to call","新界的士，或需電召")],
 "safety_en":"Stone trail slippery after rain; streams may flood — don't cross in high water; poor mobile signal mid-route.",
 "safety_zh":"雨後古道濕滑；溪澗或氾濫，水漲切勿橫過；中段電話訊號差。",
 "sources":[AFCD[10],"https://www.oasistrek.com/wilson_trail_ten.php","https://www.hkallshan.com/wilson-trail-section10/","https://www.oasistrek.com/nam_chung.php","https://www.16seats.net/eng/gmb/gn_56k.html","https://data.etabus.gov.hk/v1/transport/kmb/route/","https://timhiking.com/en/blog.php?d=191112"]
})

# fix stray blank note in stage 2
for s in stages:
    for key in ("to_start","from_end"):
        for t in s[key]:
            for k in ("note_en","note_zh"):
                if k in t and not t[k].strip(): del t[k]

trail = {"id":"wilson","name_en":"Wilson Trail","name_zh":"衞奕信徑","total_km":78,"post_prefix":"W",
 "notes":("78 km, 10 sections, Stanley Gap Road to Nam Chung. Distance posts run W001–W137 only (AFCD list), roughly every 500–650 m, not every 500 m. "
          "Harbour crossing: from W018 walk to MTR Tai Koo, Island Line to Quarry Bay, Tseung Kwan O Line to Yau Tong (Exit A1, ~1 km to W019); "
          "the official route counts the MTR ride to Lam Tin Exit A (Kwun Tong Line). Sections 3 and 8 run largely outside country parks. "
          "Section-end transport is weak at Cloudy Hill (S8/S9) and Hsien Ku Fung (S9/S10): plan descents. Emergency: 999; quote the nearest distance post."),
 "notes_zh":("全長78公里，共10段，由赤柱峽道至南涌。標距柱只有W001至W137（漁護署），間距約500–650米。"
          "過海：於W018步行往港鐵太古站，港島綫至鰂魚涌轉將軍澳綫往油塘（A1出口，步行約1公里至W019）；正式路線以藍田站A出口為第二段終點。"
          "第三、八段大部分不在郊野公園內。九龍坑山及仙姑峰均無交通接駁，須預留下山時間。緊急求助致電999，並報告最近標距柱編號。"),
 "sources":[WIKI,POSTS_PDF,"https://www.oasistrek.com/wilson_trail.php"]}

out = {"trail":trail,"stages":stages}
p="/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/research/wilson.json"
json.dump(out,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("ok", sum(s["km"] for s in stages))
