import json
import re
import ssl
import urllib.request
import urllib.parse

# Handle SSL certificate issues on macOS
try:
    _ssl_ctx = ssl.create_default_context()
except Exception:
    _ssl_ctx = ssl._create_unverified_context()

def _fetch(url: str, timeout=10):
    req = urllib.request.Request(url, headers={'User-Agent': 'CFScraper/1.0'})
    return urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx)

FANDOM_CHARACTERS = {
    'genshin impact': [
        'aether', 'lumine', 'paimon', 'amber', 'kaeya', 'lisa', 'barbara',
        'jean', 'diluc', 'razor', 'venti', 'klee', 'qiqi', 'keqing',
        'mona', 'tartaglia', 'childe', 'xiao', 'zhongli', 'albedo',
        'ganyu', 'hu tao', 'eula', 'ayaka', 'yoimiya',
        'raiden shogun', 'raiden', 'ei', 'kujou sara', 'kokomi',
        'gorou', 'itto', 'kazuha', 'sayu', 'yae miko', 'heizou',
        'ayato', 'thoma', 'nilou', 'cyno', 'dehya', 'nahida',
        'alhaitham', 'kaveh', 'wanderer', 'faruzan', 'layla', 'scaramouche',
        'dori', 'tighnari', 'collei', 'candace',
        'furina', 'focalors', 'navia', 'clorinde', 'neuvillette',
        'wriothesley', 'sigewinne', 'chiori', 'arlecchino',
        'lyney', 'lynette', 'freminet', 'charlotte',
        'xianyun', 'gaming', 'baizhu', 'yaoyao',
        'shinobu', 'shenhe', 'yun jin', 'sucrose', 'noelle', 'ningguang',
        'beidou', 'fischl', 'xiangling', 'xingqiu', 'chongyun',
        'xinyan', 'rosaria', 'yanfei', 'diona', 'aloy',
        'mualani', 'kinich', 'ajaw', 'xilonen', 'chasca',
        'ororon', 'citlali', 'mavuika', 'lan yan',
        'mizuki', 'varesa', 'iansan', 'dahlia', 'skirk',
        'columbina', 'pantalone', 'dottore', 'capitano', 'signora',
        'chevreuse', 'emilie', 'sethos', 'bennett', 'mika',
    ],
    'honkai star rail': [
        'stelle', 'caelus', 'march 7th', 'dan heng', 'himeko', 'welt',
        'bronya', 'seele', 'gepard', 'clara', 'svarog', 'serval', 'hook',
        'natasha', 'pela', 'qingque', 'tingyun', 'silver wolf', 'bailu',
        'yanqing', 'luocha', 'kafka', 'blade', 'jing yuan', 'jingliu',
        'topaz', 'numby', 'guinaifen', 'huohuo', 'argenti',
        'dr ratio', 'ratio', 'aventurine', 'robin', 'sunday',
        'firefly', 'sam', 'acheron', 'black swan', 'sparkle',
        'rappa', 'lingsha', 'feixiao', 'moze', 'jade', 'yunli',
        'xueyi', 'misha', 'gallagher', 'boothill',
        'the herta', 'aglaea', 'tribbie', 'mydei', 'castorice',
        'anaxa', 'hyacine', 'cipher', 'phainon', 'cyrene',
        'fugue', 'hanya', 'yukong', 'fu xuan', 'asta', 'arlan', 'sampo',
        'herta',
    ],
    'zenless zone zero': [
        'belle', 'wise', 'anby', 'nicole', 'billy', 'nekomata',
        'ellen', 'lycaon', 'soldier 11', 'grace', 'koleda',
        'ben', 'corin', 'piper', 'lucy', 'seth', 'qingyi',
        'jane', 'burnice', 'caesar', 'miyabi', 'yanagi',
        'harumasa', 'astra', 'lighter', 'soukaku', 'rina',
        'evelyn', 'trigger', 'hugo', 'vivian', 'pulchra',
    ],
    'nikke': [
        'red hood', 'modernia', 'scarlet', 'dorothy', 'alice',
        'crown', 'grave', 'helm', 'mast', 'centi', 'liter', 'noah',
        'sakura', 'rosanna', 'tia', 'naga', 'tove', 'jackal', 'biscuit',
        'noir', 'blanc', 'bay', 'anis', 'rapi', 'neon', 'snow white',
        'cinderella', 'marciana', 'guillotine', 'maiden', 'rei', 'anna',
        'nihilister', 'liberalio', 'ruby', 'soda', 'dolla', 'rupee',
        'maxwell', 'privaty', 'volume', 'yulha', 'elegg', 'mihara',
        'epinel', 'diesel', 'vesti', 'naira', 'eunhwa',
    ],
    'arknights': [
        'texas', 'exusiai', 'surtr', 'chen', 'bagpipe', 'mudrock',
        'rosmontis', 'skadi', 'specter', 'lappland',
        'amiya', 'siege', 'ifrit', 'eyjafjalla', 'saria', 'silence',
        'angelina', 'mostima', 'nian', 'dusk', 'ling', 'gavial',
        'nearl', 'blemishine', 'thorns', 'mountain',
        'horn', 'irene', 'goldenglow', 'fiammetta', 'penance',
        'texas alter', 'eunectes',
    ],
    'fate': [
        'artoria', 'saber', 'gilgamesh', 'merlin', 'morgan',
        'castoria', 'koyanskaya', 'melusine', 'barghest', 'ibuki',
        'musashi', 'tiamat', 'kama', 'kiara', 'ereshkigal',
        'scathach', 'skadi', 'jack', 'mordred', 'frankenstein',
        'okita', 'abigail', 'shuten', 'ibaraki', 'raikou',
        'rin tohsaka', 'senji muramasa', 'space ishtar',
        'baobhan sith', 'arcueid', 'shiki',
        'emiya', 'sieg', 'sigurd', 'bryn', 'jeanne',
    ],
    'blue archive': [
        'shiroko', 'hoshino', 'mina', 'yuuka', 'arisu', 'mutsuki',
        'asuna', 'karin', 'iroha', 'wakamo', 'nagisa', 'mika',
        'toki', 'saori', 'kayoko', 'akane', 'hifumi', 'serika',
        'izuna', 'tsubaki', 'neru', 'iori', 'aya',
        'azusa', 'koharu', 'hasumi', 'hanako', 'mashiro',
        'sakurako', 'satsuki', 'ui', 'himari', 'noa', 'rio',
        'kisaki', 'tsurugi', 'sena', 'kirino', 'misaki',
        'chinatsu', 'ayane', 'suzumi', 'shizuko', 'mimori',
        'kaho', 'hibiki', 'saki', 'marina', 'eimi',
        'kotori', 'airi', 'mari', 'arona', 'plana',
        'makoto', 'ibuki', 'megu', 'hina', 'junko',
        'momoi', 'midori', 'yuzu',
    ],
    'hololive': [
        'pekora', 'marine', 'kobo', 'moona', 'risu',
        'ollie', 'reine', 'calliope', 'gura', 'amelia', 'kiara',
        'irys', 'kronii', 'mumei', 'fauna', 'sana',
        'miko', 'aqua', 'korone', 'fubuki', 'matsuri', 'suisei',
        'subaru', 'rushia', 'noel', 'watame',
        'botan', 'luna', 'towa', 'kanata', 'coco', 'haachama',
        'gigi', 'raora', 'fuwawa', 'mococo', 'nerissa', 'shiori',
        'bijou', 'elizabeth', 'cecilia', 'dokibird',
        'laplus', 'lui', 'koyori', 'chloe', 'iroha',
        'okayu', 'mio', 'roboco', 'mel', 'aki', 'ayame', 'shion',
    ],
    'chainsaw man': [
        'denji', 'power', 'makima', 'pochita', 'aki', 'kobeni',
        'himeno', 'beam', 'quanxi', 'reze', 'angel', 'nayuta',
        'yoru', 'asami mitaka', 'fami', 'yoshida', 'fumiko',
        'katana man', 'falling devil',
    ],
    'jujutsu kaisen': [
        'gojo', 'sukuna', 'nanami', 'toji', 'megumi', 'yuji',
        'nobara', 'maki', 'geto', 'yuta', 'choso', 'yuki',
        'higuruma', 'kashimo', 'hakari', 'todo', 'panda',
        'mahito', 'jogo', 'hana', 'miwa', 'shoko',
        'kirara', 'kamo', 'naoya', 'tengen',
    ],
    'haikyuu': [
        'hinata', 'kageyama', 'oikawa', 'iwaizumi', 'bokuto',
        'akaashi', 'kuroo', 'kenma', 'sugawara', 'daichi', 'asahi',
        'nishinoya', 'tanaka', 'tsukishima', 'yamaguchi', 'ushijima',
        'tendou', 'sakusa', 'atsumu', 'osamu',
        'yachi', 'shimizu', 'komi',
    ],
    'one piece': [
        'luffy', 'zoro', 'nami', 'sanji', 'robin', 'chopper',
        'usopp', 'franky', 'brook', 'jinbe', 'yamato', 'ace', 'sabo',
        'law', 'mihawk', 'shanks', 'boa', 'kaido', 'big mom',
        'vivi', 'reiju', 'buggy', 'crocodile', 'rayleigh',
        'garp', 'smoker', 'tashigi', 'fujitora',
        'perona', 'shirahoshi',
    ],
    'hunter x hunter': [
        'gon', 'killua', 'hisoka', 'kurapika', 'chrollo',
        'leorio', 'feitan', 'nobunaga', 'phinks', 'shizuku',
        'machi', 'uvogin', 'kite', 'bisky', 'meruem',
        'komugi', 'netero', 'illumi', 'alluka',
    ],
    'bleach': [
        'ichigo', 'rukia', 'renji', 'byakuya', 'toshiro',
        'kenpachi', 'yachiru', 'aizen', 'gin', 'ulquiorra',
        'grimmjow', 'nel', 'halibel', 'stark',
        'yoruichi', 'kisuke', 'orihime', 'chad',
        'yhawch', 'ichibe', 'shunsui', 'yamamoto',
        'soifon', 'mayuri', 'nemu', 'unohana',
        'rangiku', 'shinji', 'momoi', 'kaien',
    ],
    'naruto': [
        'naruto', 'sasuke', 'sakura', 'kakashi', 'itachi', 'shisui',
        'minato', 'kushina', 'hinata', 'gaara', 'rock lee',
        'shikamaru', 'ino', 'choji', 'kiba', 'tsunade', 'jiraiya',
        'orochimaru', 'obito', 'madara', 'hashirama', 'tobirama',
        'hiruzen', 'danzo', 'deidara', 'sasori', 'kakuzu', 'hidan',
        'konan', 'pain', 'nagato', 'kabuto',
        'boruto', 'sarada', 'mitsuki', 'kawaki', 'himawari',
    ],
    'attack on titan': [
        'eren', 'mikasa', 'levi', 'armin', 'hange', 'erwin',
        'sasha', 'connie', 'jean', 'annie', 'reiner', 'berthold',
        'zeke', 'pieck', 'porco', 'gabi', 'falco', 'ymir',
        'historia', 'krista', 'grisha', 'dina',
    ],
    'demon slayer': [
        'tanjiro', 'nezuko', 'zenitsu', 'inosuke', 'giyuu',
        'shinobu', 'rengoku', 'uzui', 'mitsuri',
        'obanai', 'sanemi', 'gyomei', 'muichiro', 'genya', 'kanao',
        'muzan', 'kokushibo', 'akaza', 'daki', 'gyutaro',
        'yoriichi', 'tamayo', 'enmu', 'rui',
    ],
    'spy x family': [
        'anya', 'yor', 'loid', 'bond', 'franky',
        'yuri', 'daybreak', 'nightfall', 'fiona', 'sylvia',
    ],
    're zero': [
        'subaru', 'rem', 'ram', 'emilia', 'beatrice',
        'roswaal', 'echidna', 'satella', 'petra', 'frederica',
        'garfiel', 'otto', 'priscilla', 'crusch', 'julius',
        'reinhard', 'wilhelm', 'theresia', 'pandora',
    ],
    'kaguya-sama': [
        'kaguya', 'miyuki', 'chika', 'ishigami', 'hayasaka',
        'ai', 'kei', 'miko', 'maki', 'tsubame',
    ],
    'oshi no ko': [
        'ai hoshino', 'aqua', 'ruby', 'kana', 'akane', 'memcho',
        'gotanda', 'frill', 'melt', 'nino',
    ],
    'my hero academia': [
        'deku', 'izuku', 'bakugo', 'todoroki', 'shoto',
        'uraraka', 'all might', 'hawks', 'dabi', 'shigaraki',
        'aizawa', 'endeavor', 'mirko', 'nejire', 'tamaki', 'mirio',
        'mina', 'tsuyu', 'mineta', 'overhaul', 'stain',
        'present mic', 'midnight', 'kurogiri',
    ],
    'evangelion': [
        'shinji', 'rei', 'asuka', 'misato', 'kaworu',
        'ritsuko', 'gendo', 'yui', 'mari',
    ],
    'frieren': [
        'frieren', 'fern', 'stark', 'ubel', 'land', 'wirbel',
        'denken', 'methode', 'sense', 'sein',
        'himmel', 'heiter', 'eisen', 'flamme', 'serie',
    ],
    'mushoku tensei': [
        'rudeus', 'roxy', 'eris', 'ghislaine', 'sylphy',
        'paul', 'zenith', 'lilia', 'orsted', 'ruijerd',
        'elinalise', 'norn', 'aysha', 'hitogami',
    ],
    'dandadan': [
        'momo', 'okarun', 'seiko', 'ayase', 'aera', 'jia',
        'turbo granny', 'evil eye', 'vamola',
    ],
    'vocaloid': [
        'hatsune miku', 'miku', 'kagamine rin', 'rin',
        'kagamine len', 'len', 'megurine luka', 'luka',
        'gumi', 'kaito', 'meiko', 'tet', 'piko',
    ],
    'touhou': [
        'reimu', 'marisa', 'cirno', 'flandre', 'sakuya',
        'remilia', 'patchouli', 'yukari', 'youmu', 'yuyuko',
        'sanae', 'suwako', 'kanako', 'alice', 'aya',
        'koishi', 'satori', 'tenshi', 'byakuren',
    ],
    'persona': [
        'joker', 'morgana', 'ryuji', 'ann', 'yusuke',
        'makoto', 'futaba', 'haru', 'akechi', 'maruki',
        'yu', 'yosuke', 'chie', 'kanji', 'naoto',
        'rise', 'teddie', 'adachi',
    ],
    'bungo stray dogs': [
        'dazai', 'chuuya', 'atsushi', 'akutagawa', 'fukuzawa',
        'mori', 'tanizaki', 'kenji', 'higuchi',
        'kyoka', 'yosano', 'ranpo', 'poe', 'lucy',
        'sigma', 'gogol', 'nikolai', 'fukushi',
    ],
    'mobile legends': [
        'ling', 'lance', 'claude', 'hayabusa', 'fanny',
        'gusion', 'selena', 'karina', 'lunox', 'guinevere',
        'lesley', 'beatrix', 'granger', 'vale', 'xavier',
        'chou', 'paquito', 'silvanna', 'esmeralda',
        'angela', 'rafaela', 'estes', 'natalia', 'saber',
    ],
    'valorant': [
        'jett', 'phoenix', 'reyna', 'raze', 'sage',
        'viper', 'omen', 'breach', 'killjoy', 'cypher',
        'kayo', 'skye', 'yoru', 'astra', 'neon',
        'chamber', 'fade', 'harbor', 'gekko',
        'deadlock', 'iso', 'clove', 'vyse', 'tejo', 'waylay',
    ],
    'solo leveling': [
        'sung jinwoo', 'jin woo', 'cha haein', 'cha hae',
        'esil', 'igris', 'baek', 'go gunhee', 'thomas',
        'beru', 'tusk',
    ],
    'sanrio': [
        'cinnamoroll', 'kuromi', 'my melody', 'pompompurin',
        'hello kitty', 'pochaco', 'gudetama', 'aggretsuko',
        'badtz maru', 'keroppi', 'chococat',
    ],
    'pokemon': [
        'pikachu', 'eevee', 'charizard', 'gengar', 'umbreon',
        'espeon', 'sylveon', 'mew', 'mimikyu', 'jolteon',
        'flareon', 'vaporeon', 'leafeon', 'glaceon', 'rayquaza',
        'mewtwo', 'lugia', 'arceus', 'dragonite', 'gardevoir',
        'lucario', 'greninja', 'sprigatito', 'fuecoco', 'quaxly',
        'snorlax', 'ditto', 'magikarp', 'gyarados',
    ],
    'love live': [
        'honoka', 'eli', 'kotori', 'umi', 'rin', 'maki',
        'hanayo', 'nico', 'nozomi', 'chika', 'you', 'rikko',
        'kanan', 'diae', 'mari', 'ruby', 'yoshiko',
        'kanon', 'keke', 'chisato', 'sumire', 'ren',
    ],
    'uma musume': [
        'special week', 'silence suzuka', 'tokai teio', 'mejiro mcdowell',
        'oguri cap', 'kitasan black', 'satono diamond', 'vodka',
        'maruzensky', 'el condor pasa', 'super creek', 'nice nature',
        'urara', 'tamamo cross', 'manhattan cafe', 'rice shower',
        'mayano top', 'narita brian', 'biwa hayate',
        'agnes tachyon', 'seeking the gold', 'inari one',
    ],
    'bang dream': [
        'kasumi', 'arisa', 'saaya', 'rimi', 'kokoro',
        'kaoru', 'hagumi', 'misaki', 'michelle',
        'rani', 'moca', 'himari', 'tomoe', 'tsugumi',
        'aya', 'hina', 'chisato', 'maya', 'eve',
        'yukina', 'sayo', 'lisa', 'ako', 'rinko',
    ],
    'project sekai': [
        'ichika', 'saki', 'honami', 'shiho', 'minori',
        'haruka', 'airi', 'shizuku', 'kohane',
        'an', 'akito', 'toya', 'tsukasa', 'emu',
        'nene', 'rui', 'marina',
    ],
    'sword art online': [
        'kirito', 'asuna', 'sinon', 'leafa', 'yuuki',
        'alice', 'eugeo', 'kayaba', 'yui',
        'klein', 'agil', 'silica', 'lizbet',
    ],
    'konosuba': [
        'kazuma', 'aqua', 'megumin', 'darkness', 'lalatina',
        'yun yun', 'wiz', 'vanir', 'eiris',
    ],
    'overlord': [
        'ainz', 'albedo', 'shalltear', 'demiurge', 'coctyus',
        'mare', 'aura', 'sebas', 'nebra',
        'clementine', 'brain',
    ],
    'tensura': [
        'rimuru', 'milim', 'benimaru', 'shuna', 'shion',
        'diablo', 'veldora', 'chloe', 'hinata',
        'gobta', 'soei', 'geld', 'hakuro',
    ],
    'danmachi': [
        'bell', 'aiz', 'hestia', 'lili', 'ryu',
        'eina', 'freya', 'haruhime', 'ais',
    ],
    'code geass': [
        'lelouch', 'suzaku', 'c2', 'kallen', 'nunally',
        'euphemia', 'cornelia', 'schneizel',
        'jeremiah', 'roro', 'sayoko',
    ],
    'tokyo revengers': [
        'takemichi', 'mikey', 'draken', 'chifuyu',
        'baji', 'kisaki', 'hina', 'emma',
        'senju', 'south', 'kakugo',
    ],
    'kaiju no 8': [
        'kafka', 'reno', 'mina', 'hoshina', 'kikoru',
        'narumi', 'haruichi', 'ishihara',
    ],
    'dungeon meshi': [
        'laios', 'marcille', 'chilchuck', 'senshi',
        'falin', 'izutsumi', 'namari', 'shuro',
    ],
    'sakamoto days': [
        'taro sakamoto', 'shin', 'lu', 'aoi', 'hana',
        'nagumo', 'kindaka', 'osaragi', 'takamura',
    ],
    'sao': [],  # alias for sword art online
    'kny': [],  # alias for demon slayer
    'jjk': [],  # alias for jujutsu kaisen
    'csm': [],  # alias for chainsaw man
    'hxh': [],  # alias for hunter x hunter
    'mha': [],  # alias for my hero academia
    'aot': [],  # alias for attack on titan
    'hsr': [],  # alias for honkai star rail
    'zzz': [],  # alias for zenless zone zero
    'fgo': [],  # alias for fate
    'priconne': [],  # alias for princess connect
    'imas': [],  # alias for idolmaster
    'proseka': [],  # alias for project sekai
    'lovelive': [],  # alias for love live
    'bsd': [],  # alias for bungo stray dogs
    'reincarnated slime': [],  # alias for tensura
    'edgerunners': [],  # alias for cyberpunk edgerunners
}

ALIASES = {
    'sao': 'sword art online', 'kny': 'demon slayer', 'kimetsu': 'demon slayer',
    'jjk': 'jujutsu kaisen', 'csm': 'chainsaw man', 'csms': 'chainsaw man',
    'hxh': 'hunter x hunter', 'mha': 'my hero academia', 'hero academia': 'my hero academia',
    'aot': 'attack on titan', 'shingeki': 'attack on titan',
    'hsr': 'honkai star rail', 'star rail': 'honkai star rail',
    'zzz': 'zenless zone zero', 'zenless': 'zenless zone zero',
    'fgo': 'fate', 'grand order': 'fate',
    'priconne': 'princess connect', 're:dive': 'princess connect',
    'imas': 'idolmaster', 'idolm@ster': 'idolmaster',
    'proseka': 'project sekai', 'sekai': 'project sekai',
    'lovelive': 'love live', 'll': 'love live',
    'bsd': 'bungo stray dogs',
    'tensura': 'tensura', 'reincarnated slime': 'tensura', 'slime': 'tensura',
    'edgerunners': 'cyberpunk edgerunners', 'cyberpunk': 'cyberpunk edgerunners',
    'mlbb': 'mobile legends', 'ml': 'mobile legends',
}

# Build alias references
for alias, target in ALIASES.items():
    if alias not in FANDOM_CHARACTERS and target in FANDOM_CHARACTERS:
        FANDOM_CHARACTERS[alias] = FANDOM_CHARACTERS[target]

KNOWN_TITLES = {
    'heaven officials blessing': 'Heaven Official\'s Blessing',
    'grandmaster of demonic cultivation': 'Grandmaster of Demonic Cultivation',
    'mo dao zu shi': 'Grandmaster of Demonic Cultivation',
    'tgcf': 'Heaven Official\'s Blessing',
    'mdzs': 'Grandmaster of Demonic Cultivation',
    'scum villain': 'Scum Villain Self-Saving System',
    'svsss': 'Scum Villain Self-Saving System',
    'heated rivalry': 'Heated Rivalry',
    'the game is life': 'The Game is Life',
    'check please': 'Check Please',
    'hockey rpf': '',
}

CACHE = {}


def normalize_fandom(name: str) -> str:
    n = name.strip().lower()
    if n in ALIASES:
        n = ALIASES[n]
    return n


def search_local(name: str) -> list[str] | None:
    n = normalize_fandom(name)
    if n in FANDOM_CHARACTERS:
        chars = FANDOM_CHARACTERS[n]
        return chars if chars else None
    # Partial match with word boundaries — only match on multi-word keys (>=4 chars)
    # to avoid short aliases like "ll" matching unrelated words
    n_words = set(n.split())
    for key, chars in FANDOM_CHARACTERS.items():
        if len(key) < 4:
            continue
        if n in key or key in n:
            return chars if chars else None
        key_words = set(key.split())
        if n_words & key_words:
            return chars if chars else None
    return None


def search_wikipedia(name: str) -> list[dict]:
    """Search Wikipedia for characters from a fandom. Returns list of {name, confidence}."""
    if name in CACHE:
        return CACHE[name]

    query = urllib.parse.quote(name + ' characters')
    search_url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=3'

    try:
        res = _fetch(search_url)
        data = json.loads(res.read())
        pages = data.get('query', {}).get('search', [])
    except Exception:
        CACHE[name] = []
        return []

    for page in pages:
        title = page['title']
        if 'list' in title.lower() and 'character' in title.lower():
            chars = _parse_character_list(title, name)
            if chars:
                CACHE[name] = chars
                return chars

    # Try first result anyway
    for page in pages[:2]:
        title = page['title']
        chars = _parse_character_list(title, name)
        if chars:
            CACHE[name] = chars
            return chars

    CACHE[name] = []
    return []


def _parse_character_list(page_title: str, fandom: str) -> list[dict]:
    """Parse Wikipedia page for character names."""
    title = urllib.parse.quote(page_title)
    url = f'https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={title}&format=json'

    try:
        res = _fetch(url)
        data = json.loads(res.read())
        pages = data.get('query', {}).get('pages', {})
        extract = ''
        for pid, pdata in pages.items():
            if pid != '-1':
                extract = pdata.get('extract', '')
                break
    except Exception:
        return []

    if not extract:
        return []

    chars = []
    seen = set()
    fandom_lower = fandom.lower()

    # Pattern 1: lines starting with * (bullet lists)
    for line in extract.split('\n'):
        line = line.strip()
        if line.startswith('*') or line.startswith('#'):
            item = line.lstrip('*# ').strip()
            # Extract bold-wrapped names
            bold_names = re.findall(r"'''(.*?)'''", item)
            for bn in bold_names:
                bn = bn.strip()
                if len(bn) < 2 or bn.lower() in seen:
                    continue
                if any(ignore in bn.lower() for ignore in ['see also', 'references', 'notes', 'design', 'concept']):
                    continue
                if len(bn.split()) > 4:
                    continue
                seen.add(bn.lower())
                chars.append({'name': bn, 'source': 'wikipedia'})
            # If no bold, take item prefix before comma or parentheses
            if not bold_names and item and len(item) > 2:
                name = item.split(',')[0].split('(')[0].strip()
                if name and len(name) > 2 and name.lower() not in seen:
                    if not any(ignore in name.lower() for ignore in ['the ', 'this ', 'list ', 'main ', 'also ']):
                        seen.add(name.lower())
                        chars.append({'name': name, 'source': 'wikipedia'})

    # Pattern 2: tables | separated (common in anime character tables)
    table_matches = re.findall(r'\|\s*(\w[\w ]{1,30}?)\s*\|\|\s*', extract)
    for m in table_matches:
        m = m.strip()
        if 2 < len(m) < 30 and m.lower() not in seen:
            if not any(ignore in m.lower() for ignore in ['episode', 'chapter', 'volume', 'voice', 'japanese', 'english']):
                seen.add(m.lower())
                chars.append({'name': m, 'source': 'wikipedia'})

    return chars[:50]
