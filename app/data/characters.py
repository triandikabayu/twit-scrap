import os
import re
import sys
from collections import Counter
from datetime import datetime

import pandas as pd


CSV_PATH = 'data/comifuro_tweets.csv'
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

ISO_PATTERNS = re.compile(
    r'(?:(?:cari|nyari|nc|mau beli|pengen beli|ada yang jual|looking for|where.*?buy|recommend)|'
    r'\b(wtb|wts|lf|iso)\b)',
    re.IGNORECASE
)

NOISE_WORDS = {
    'booth', 'tiket', 'ticket', 'merch', 'merchandise', 'single', 'preorder',
    'po', 'dong', 'dongg', 'kak', 'kakk', 'bang', 'bro', 'sis', 'mas', 'mbak',
    'harga', 'info', 'infokan', 'share', 'sharee', 'pliss', 'pls', 'please',
    'guys', 'kawan', 'temen', 'teman', 'ga', 'gak', 'gk', 'ngga', 'enggak',
    'bisa', 'gak', 'ada', 'di', 'ke', 'sih', 'deh', 'lah', 'yah', 'ya',
    'sapa', 'siapa', 'yang', 'juga', 'lagi', 'aja', 'a', 'the', 'at', 'for',
    'comifuro', 'cf22', 'cf', 'comipara', 'day', 'day1', 'day2', 'jual', 'beli',
    'cari', 'nyari', 'wtb', 'wts', 'lf', 'iso', 'nc', 'trading', 'trade',
    'vtuber', 'fanmade', 'fandom', 'katalog', 'brand', 'acara', 'event',
    'pax', 'rugi', 'adm', 'fee', 'dm', 'link', 'shopee', 'tokped',
    'slot', 'order', 'commission', 'comm', 'wt', 'jastip', 'titip',
    # Noise kata umum
    'ini', 'itu', 'saja', 'sudah', 'telah', 'akan', 'bisa', 'dapat',
    'tahun', 'bulan', 'minggu', 'hari', 'kemarin', 'besok', 'nanti',
    'baru', 'lama', 'banyak', 'sedikit', 'besar', 'kecil',
    'suka', 'sayang', 'mau', 'pengen', 'pake', 'pakai', 'punya',
    'namun', 'tapi', 'tetapi', 'sedangkan', 'sementara', 'karena',
    'jakarta', 'bandung', 'surabaya', 'jogja', 'yogya', 'bogor',
    'depok', 'tangsel', 'bekasi', 'jabodetabek', 'pusat', 'selatan',
    'utara', 'timur', 'barat', 'tengah',
    'you', 'your', 'our', 'their', 'this', 'that', 'these', 'those',
    'also', 'even', 'still', 'well', 'just', 'like', 'very', 'much',
    'may', 'june', 'july', 'august', 'april', 'maret', 'january',
    'february', 'march', 'september', 'october', 'november', 'december',
    'senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu',
    'lol', 'wkwk', 'wkwkwk', 'haha', 'hehe', 'xixi', 'huhu', 'hmm',
    'btw', 'otw', 'cmiiw', 'imo', 'imho', 'afaik', 'idk', 'tbh',
    'ya', 'iya', 'kalo', 'kalau', 'karna', 'karena', 'soalnya',
    'gue', 'gw', 'lo', 'lu', 'kita', 'kami', 'mereka',
    # Game/event names (not characters)
    'hoyoverse', 'mihoyo', 'bandai', 'namco', 'sega', 'nintendo',
    'deltarune', 'undertale', 'fate', 'hololive', 'lovelive',
    'hearthstone', 'dota', 'valve', 'riot', 'epic',
    # Genres / tags (not characters)
    'yuri', 'yaoi', 'doujin', 'doujinshi', 'fanmerch', 'fanart',
    'fanmade', 'original', 'orivoca', 'voca',
    # Book/media names (not characters)
    'hail', 'phm', 'project hail mary', 'orv',
    'omniscient reader',

    'bl', 'gl', 'lgbt', 'lgbtq', 'pride', 'queer',
    'anime', 'manga', 'game', 'gacha', 'otome',
    # False positives umum dari tweet
    'knight', 'knights', 'princess', 'prince', 'queen', 'king',
    'love', 'like', 'hate', 'want', 'need',
    'because', 'especially', 'however', 'therefore', 'furthermore',
    'moreover', 'meanwhile', 'otherwise', 'nevertheless',
    'aftersale', 'aftermarket', 'after', 'before',
    'catalog', 'catalogue', 'catalogs', 'stickers', 'sticker',
    'poster', 'posters', 'photo', 'photos', 'picture', 'pictures',
    'project', 'impact', 'universe', 'world', 'series',
    'masih', 'tetapi', 'terutama', 'setelah', 'sebelum',
    'sedangkan', 'sementara', 'sehingga', 'karena', 'namun',
    'tawarin', 'tawaran', 'ditawar', 'nego', 'negosiasi',
    'sample', 'contoh', 'display', 'displayed',
    'bundle', 'bundling', 'package', 'packaging',
    'order', 'orders', 'ordered', 'preorder', 'preorderr',
    'ready', 'stock', 'stocks', 'limited', 'exclusive',
    'special', 'discount', 'promo', 'voucher', 'coupon',
    'freebie', 'freebies', 'bonus', 'extra',
    'message', 'inbox', 'inquiry', 'inquiries',
    'comment', 'mention', 'reply', 'retweet', 'quote',
    'follow', 'followers', 'following', 'profile',
    'prize', 'price', 'prices', 'pricing',
    'shipping', 'delivery', 'courier', 'tracking',
    'condition', 'quality', 'original', 'genuine', 'authentic',
    'sealed', 'brand', 'mint', 'perfect', 'excellent',
    'urgent', 'important', 'serious', 'legit', 'trusted',
    'seller', 'buyer', 'shipper', 'admin', 'adm', 'oc', 'oc)',
    'payment', 'transfer', 'deposit', 'invoice', 'receipt',
    'warranty', 'guarantee', 'refund', 'exchange', 'return',
    'express', 'regular', 'economy', 'instant',
    'interested', 'interest', 'reserve', 'reserved',
    'sold', 'bought', 'listed', 'available',
    'update', 'reminder', 'deadline', 'bump',
    'nice', 'beautiful', 'cute', 'adorable', 'lovely', 'pretty',
    'cool', 'awesome', 'amazing', 'fantastic', 'wonderful',
    'gorgeous', 'stunning', 'splendid', 'excellent',
    'semoga', 'moga', 'mudah', 'cepat', 'laku',
    'baru', 'lama', 'besar', 'kecil', 'bagus', 'jelek',
    'indah', 'enak', 'manis', 'panas', 'dingin',
    'malam', 'siang', 'pagi', 'sore', 'petang',
    'waktu', 'tanggal', 'bulan', 'tahun',
    'semua', 'banyak', 'sedikit', 'beberapa',
    'tentang', 'antara', 'melalui', 'untuk',
    'dapat', 'harus', 'boleh', 'mungkin',
    'sekitar', 'kurang', 'lebih', 'paling', 'sangat',
    'selalu', 'jarang', 'sering', 'kadang',
    'comifuro', 'comipara', 'comic frontier',
    'booth', 'booths', 'event', 'acara',
    'pameran', 'festival', 'convention', 'con',
    'jastip', 'titip', 'trading', 'trade', 'trades',
    'open order', 'close order', 'slot', 'slots',
    'fanmade', 'fanmerch', 'merch', 'merchandise',
    'preferably', 'preferable', 'preference', 'preferences',
    'anything', 'anyone', 'anybody', 'anywhere',
    'everything', 'everyone', 'everybody', 'everywhere',
    'somewhere', 'somebody', 'someone', 'sometime',
    'nowhere', 'nothing', 'nobody', 'none',
    'already', 'always', 'almost', 'also', 'though',
    'however', 'whatever', 'whenever', 'wherever',
    'moreover', 'furthermore', 'meanwhile', 'otherwise',
    'nevertheless', 'nonetheless', 'notwithstanding',
    'therefore', 'thereby', 'therein', 'thereafter',
    'henceforth', 'hence', 'thus', 'thence',
    'furthermore', 'further', 'besides', 'likewise',
    'similarly', 'conversely', 'accordingly',
    'definitely', 'absolutely', 'certainly', 'surely',
    'probably', 'possibly', 'potentially', 'eventually',
    'ultimately', 'generally', 'typically', 'usually',
    'frequently', 'occasionally', 'seldom', 'rarely',
    'practically', 'basically', 'essentially',
    'particularly', 'specifically', 'especially',
    'significantly', 'considerably', 'substantially',
    'approximately', 'roughly', 'nearly', 'virtually',
    'meanwhile', 'late', 'early', 'soon', 'later',
    'earlier', 'sooner', 'ago', 'since', 'still',
    'yet', 'already', 'anyway', 'anyhow', 'anyways',
    'maybe', 'perhaps', 'probably', 'indeed',
    'surely', 'certainly', 'definitely',
    'please', 'pliss', 'plis', 'plisss',
    'maybe', 'perhaps', 'possible', 'perhaps',
    'please', 'kindly', 'nicely', 'gently',
    'urgent', 'emergency', 'critical', 'important',
    'besok', 'kemarin', 'nanti', 'tadi', 'ini', 'itu',
    'disini', 'disana', 'distu', 'disitu',
    'hope', 'hopes', 'hoped', 'hoping',
    'version', 'versions', 'ver', 'part', 'parts',
    'chapter', 'chapters', 'volume', 'volumes', 'episode',
    'season', 'series', 'edition', 'editions',
    'type', 'types', 'variant', 'variants',
    'anyang', 'selamat', 'siang', 'malam', 'pagi',
    'kaka', 'kakak', 'adek', 'adik', 'om', 'tante',
    'dakimakura', 'totebag', 'photocard', 'deskmat', 'artprint',
    'standee', 'keychain', 'gantungan', 'aksesoris', 'figurine',
    'cardboard', 'akrilik', 'acrylic', 'miniature',
    'sticker', 'stickers', 'stiker', 'shikishi',
    'musume', 'makura', 'dakimura',
    'priority', 'diutamakan', 'prioritas',
    'originals', 'original', 'sunday', 'monday',
    'booking', 'reserve', 'reserved',
    'midori', 'green', 'white', 'black', 'blue', 'red', 'pink',
    'colour', 'color', 'colors', 'colours',
    'oc', 'ocs', 'oc)', 'original character',
    'code', 'related', 'include', 'include',
    'diaries', 'book', 'books', 'reading',
    'endfield', 'field', 'work', 'project',
    'fast', 'easy', 'safe', 'cheap', 'best',
    'indonesia', 'indonesian',
    'haru', 'harus',
    'bubble', 'wrap', 'packaging', 'pack',
    'types', 'type', 'variant', 'variants',
    'waifu', 'husbando', 'husband',
    'holding', 'background', 'pouches', 'missing', 'mendapat',
    'nijisanji', 'anycolor', 'stamp', 'stamps', 'shipped',
    'changing', 'kamisama', 'jellyfish', 'highschool', 'medalis',
    'choco', 'chocolate', 'marshmallow', 'bubble',
    'gintama', 'akshsjdhd', 'hanya',
}

URGENCY_WORDS = {
    # Desperate (3)
    'desperate': 3, 'butuh banget': 3, 'nyari banget': 3,
    'cari mati-matian': 3, 'cari mati2an': 3,
    'plis bgt': 3, 'plis banget': 3, 'pliss banget': 3,
    'cari dari kmrn': 3, 'cari dari kemaren': 3, 'cari dari kemarin': 3,
    'nyari dari kmrn': 3, 'nyari dari kemaren': 3,
    'dm me please': 3, 'pengen bgt': 3, 'pingin bgt': 3,
    'butuh bgt': 3, 'butuh banget': 3, 'nyari bgt': 3,
    # High (2)
    'please': 2, 'plis': 2, 'pliss': 2, 'banget': 2,
    'cari dong': 2, 'nyari dong': 2, 'tolong': 2,
    'ada yg jual': 2, 'ada yang jual': 2, 'ada gak': 2,
    'mau banget': 2, 'butuh': 2, 'butuh bgt': 2,
    'siapa yg jual': 2, 'ada yg punya': 2, 'ada yg jual gak': 2,
    # Normal (1)
    'wtb': 1, 'wtt': 1, 'nc': 1, 'iso': 1, 'lf': 1,
    'cari': 1, 'nyari': 1, 'mau beli': 1, 'pengen beli': 1,
    'looking for': 1, 'open iso': 1, 'dm': 1, 'dm me': 1,
    'want to buy': 1, 'wants to buy': 1,
}

KNOWN_CHARACTERS = {
    # --- Genshin Impact ---
    'aether', 'lumine', 'paimon', 'amber', 'kaeya', 'lisa', 'barbara',
    'jean', 'diluc', 'razor', 'venti', 'klee', 'qiqi', 'keqing',
    'mona', 'tartaglia', 'childe', 'xiao', 'zhongli', 'albedo',
    'ganyu', 'hu tao', 'eula', 'ayaka', 'kamisato ayaka', 'yoimiya',
    'raiden', 'raiden shogun', 'ei', 'kujou sara', 'kokomi',
    'sangonomiya kokomi', 'gorou', 'itto', 'ararara itto',
    'kazuha', 'kaedehara kazuha', 'sayu', 'yae miko', 'heizou',
    'shikanoin heizou', 'ayato', 'kamiasto ayato', 'thoma',
    'nilou', 'cyno', 'dehya', 'nahida', 'alhaitham', 'kaveh',
    'wanderer', 'faruzan', 'layla', 'scaramouche', 'dori',
    'tighnari', 'collei', 'candace', 'nilou',
    'furina', 'focalors', 'navia', 'clorinde', 'neuvillette',
    'wriothesley', 'sigewinne', 'chiori', 'arlechino', 'arlecchino',
    'lyney', 'lynette', 'freminet', 'charlotte',
    'xianyun', 'gaming', 'xiao', 'baizhu', 'yaoyao',
    'kuki', 'kuki shinobu', 'nilou',
    'mualani', 'kinich', 'ajaw', 'xilonen', 'chasca',
    'ororon', 'citlali', 'mavuika', 'lan yan',
    'shenhe', 'yun jin', 'yunjin', 'sucrose', 'noelle', 'ningguang',
    'beidou', 'fischl', 'xiangling', 'xingqiu', 'chongyun',
    'xinyan', 'rosaria', 'yanfei', 'shinobu',
    'diona', 'aloy', 'traveler',
    'columbina', 'damselette', 'pantalone', 'pierro', 'dottore',
    'signora', 'la signora', 'capitano', 'pulcinella', 'sandrone',
    'arvind',
    'mizuki', 'varesa', 'iansan', 'dahlia', 'skirk', 'effie',
    'si noe', 'kuki shinobu', 'shinobu', 'mika', 'kipac', 'clorinde',
    'chevreuse', 'emilie', 'sethos', 'kaveh', 'layla', 'faruzan',
    'dori', 'heizou', 'shikanoin heizou', 'gorou', 'thoma',
    'yunjin', 'yun jin', 'bennett', 'fischl', 'razor', 'chongyun',

    # --- Honkai Star Rail ---
    'stelle', 'caelus', 'march 7th', 'dan heng', 'himeko',
    'welt', 'bronya', 'seele', 'gepard', 'clara', 'svarog',
    'serval', 'hook', 'natasha', 'pela', 'pela', 'qingque',
    'tingyun', 'fugue', 'silver wolf', 'bailu', 'yanqing',
    'luocha', 'kafka', 'blade', 'jing yuan', 'jingliu',
    'topaz', 'numby', 'guinaifen', 'huohuo', 'argenti',
    'dr ratio', 'ratio', 'aventurine', 'robin', 'sunday',
    'firefly', 'sam', 'acheron', 'black swan', 'sparkle',
    'rappa', 'lingsha', 'feixiao', 'moze', 'jade', 'yunli',
    'xueyi', 'misha', 'gallagher', 'boothill',
    'screwllum', 'stephen', 'polka',
    'herta', 'asta', 'arlan', 'pela', 'hook', 'natasha',
    'sampo', 'serval', 'gepard', 'bronya', 'seele', 'bailu',
    'yanqing', 'welt', 'himeko', 'clara', 'svarog',
    'the herta', 'aglaea', 'tribbie', 'mydei', 'castorice',
    'anaxa', 'hyacine', 'cipher', 'phainon', 'cyrene',
    'mr reca', 'big herta', 'sapphire', 'conductor',
    'hanya', 'yukong', 'fu xuan', 'swordmaster', 'march',

    # --- Zenless Zone Zero ---
    'belle', 'wise', 'anby', 'nicole', 'billy', 'nekomata',
    'ellen', 'lycaon', 'soldier 11', 'grace', 'koleda',
    'ben', 'corin', 'piper', 'lucy', 'seth', 'qingyi',
    'jane', 'burnice', 'caesar', 'miyabi', 'yanagi',
    'harumasa', 'astra', 'lighter', 'soukaku', 'rina',
    'evelyn', 'trigger', 'hugo', 'vivian', 'pulchra',
    'big daddy', 'snap', 'francis', 'belldog', 'sandrock',
    'baddie', 'pirate', 'scorcher', 'cradle', 'luna',
    'sharkboo', 'resonia', 'bangboo', 'belobog', 'butler',
    'moccus', 'black boar', 'avacado', 'propeller', 'sumo',

    # --- NIKKE ---
    'red hood', 'modernia', 'scarlet', 'dorothy', 'alice',
    'marciana', 'crown', 'grave', 'helm', 'mast', 'centi',
    'liter', 'noah', 'sakura', 'rosanna', 'tia', 'naga',
    'tove', 'jackal', 'biscuit', 'noir', 'blanc', 'bay',
    'hecate', 'rapture', 'anis', 'rapi', 'neon', 'snow white',
    'brid', 'signal', 'isabel', 'viper', 'sin', 'quency',
    'guillotine', 'maiden', 'rei', 'anna', 'cinderella',
    'grave', 'sbs', 'rumani',
    'nihilister', 'liberalio', 'indivilia', 'chatterbox',
    'mihara', 'epinel', 'diesel', 'mica', 'belorta',
    'dolla', 'rupee', 'yuni', 'soline', 'ether', 'delta',
    'vesti', 'naira', 'eunhwa', 'anima', 'mary', 'crow',
    'ludmilla', 'yulha', 'elegg', 'soda', 'cocoa', 'frima',
    'maxwell', 'privaty', 'volume', 'admi', 'milk', 'sugar',
    'yan', 'xmas', 'fugue', 'grave digger', 'smol white',

    # --- Arknights ---
    'texas', 'exusiai', 'surtr', 'chen', 'bagpipe', 'mudrock',
    'eunectes', 'rosmontis', 'skadi', 'specter', 'lappland',
    'amiya', 'siege', 'ifrit', 'eyjafjalla', 'saria', 'silence',
    'angelina', 'mostima', 'nian', 'dusk', 'ling', 'gavial',
    'nearl', 'blemishine', 'thorns', 'mountain', 'eijafjalla',
    'horn', 'irene', 'goldenglow', 'fiammetta', 'penance',
    'gavial alter', 'texas alter', 'neca', 'warzilla', 'estelle',
    'utage', 'bubble', 'matterhorn', 'vulcan', 'frostleaf',
    'savage', 'cardigan', 'vanilla', 'plume', 'fangg', 'addle',
    'nightmare', 'deepcolor', 'brown', 'conviction',
    'tuye', 'whislash', 'whitney', 'melenta', 'swire',
    'dobermann', 'mousse', 'jessica', 'liskarm', 'franka',

    # --- Fate ---
    'castoria', 'koyanskaya', 'melusine', 'barghest', 'ibuki',
    'musashi', 'tiamat', 'space ishtar', 'senji muramasa',
    'kama', 'kiara', 'sitonai', 'ereshkigal', 'iskandar',
    'artoria', 'saber', 'rin tohsaka', 'gilgamesh', 'enki',
    'merlin', 'morgan', 'baobhan sith', 'scathach', 'skadi',
    'jarcher', 'bryn', 'nursery rhyme', 'jack',
    'shiki', 'void shiki', 'saber shiki', 'arcueid',
    'miyu', 'chloe', 'illya', 'irisviel', 'maid alter',
    'lartoria', 'lalter', 'jalter', 'summer jalter',
    'mhx', 'mhxx', 'saber alter', 'santa alter',
    'mordred', 'frankenstein', 'jack', 'swimsuit musashi',
    'okita', 'okita alter',     'nobus keiji', 'maou nobu',
    'abigail', 'lavinia', 'hokusai', 'yang guifei',
    'van gogh', 'molay', 'galatea', 'brihildr',
    'sigurd', 'sieg', 'siegfried', 'kerry', 'emiya',
    'irori', 'caren', 'amakusa', 'semiramis',
    'shuten', 'ibaraki', 'tomoe', 'minamoto', 'raikou',

    # --- Blue Archive ---
    'shiroko', 'hoshino', 'mina', 'yuuka', 'arisu', 'mutsuki',
    'asuna', 'karin', 'iroha', 'wakamo', 'nagisa', 'mika',
    'toki', 'saori', 'kayoko', 'akane', 'hifumi', 'serika',
    'izuna', 'tsubaki', 'neru', 'iori', 'aya',
    'azusa', 'koharu', 'hasumi', 'hanako', 'mashiro',
    'sakurako', 'satsuki', 'ui', 'himari', 'noa', 'rio',
    'kisaki', 'tsurugi', 'sena', 'kirino', 'misaki',
    'moe', 'shigure', 'michiru', 'kaede', 'ogata',
    'chinatsu', 'ayane', 'suzumi', 'shizuko', 'mimori',
    'kaho', 'hibiki', 'saki', 'marina', 'eimi',
    'rui', 'kotori', 'airi', 'mari', 'arona', 'plana',
    'key', 'shiroko terror', 'shiroko*terror', 'mika', 'seia',
    'fubuki', 'chise', 'kikyou', 'shinon', 'satsuki',
    'makoto', 'ibuki', 'megu', 'hina', 'akari', 'junko',
    'jingai', 'haruka', 'misaki', 'shinon', 'michiru',
    'nodoka', 'shizuko', 'oboro', 'shiromi', 'momoi',
    'midori', 'yuzu', 'asuna', 'neru', 'karin', 'kayoko',
    'mutsuki', 'akari', 'junko', 'haruka', 'misaki',
    'hovercraft', 'yoshimi', 'reijo', 'maestro', 'kureha',

    # --- Hololive / VTuber ---
    'pekora', 'marine', 'kobo', 'anya', 'moona', 'risu',
    'ollie', 'reine', 'calliope', 'gura', 'amelia', 'kiara',
    'irys', 'kronii', 'mumei', 'fauna', 'sana', 'fuwa fuwa',
    'dokibird', 'miko', 'sakura miko', 'aqua', 'minato aqua',
    'korone', 'fubuki', 'matsuri', 'suisei', 'hoshimachi suisei',
    'subaru', 'pekora', 'rushia', 'flaren', 'noel', 'watame',
    'botan', 'luna', 'towa', 'kanata', 'coco', 'haachama',
    'gigi', 'raora', 'fuwawa', 'mococo', 'nerissa', 'shiori',
    'bijou', 'elizabeth', 'cecilia', 'rissa', 'nerissa ravencroft',
    'biboo', 'fuwa mococo', 'fw mc', 'gigi murin', 'rachelle',
    'reine', 'vestia', 'zeta', 'kaela', 'kovalskia',
    'irys', 'mumei', 'kronii', 'fauna', 'sana', 'bae',
    'hakos baelz', 'nanashi mumei', 'ceres fauna',
    'ouro kronii', 'tsukumo sana',
    'laplus', 'lui', 'koyori', 'chloe', 'iroha',
    'okayu', 'mio', 'roboco', 'mel', 'aki', 'haachama',
    'ayame', 'shion', 'choco', 'shishiro botai',
    'pavolia reine', 'vestia zeta', 'kobo kanaeru',
    'kureiji ollie', 'anyo melfissa',
    'mori calliope', 'gawr gura', 'ninomae inanis',
    'takane lui', 'yogiri', 'hiodoshi ao', 'aoi doto',
    'fujio clara', 'sakamata chloe', 'kazama iroha',
    'rikka', 'sasaki saku', 'alfariz', 'ex albio',
    'nagi', 'rana', 'hada', 'amagase', 'hanabata',
    'achan', 'uiha', 'seto', 'mannen', 'enma', 'arakawa',
    'rose', 'rinda', 'layla', 'veronica', 'rara', 'abbbb',

    # --- Chainsaw Man ---
    'power', 'makima', 'pochita', 'asami mitaka', 'yoru',
    'denji', 'aki', 'kobeni', 'himeno', 'beam', 'quanxi',
    'reze', 'angel', 'pochita', 'nayuta',
    'katana man', 'bleeze', 'fami', 'falling devil',
    'justice', 'fire devil', 'barn owl', 'barem',
    'haruka', 'daido', 'nobara', 'benisuzume', 'yoshida',
    'fumiko', 'spear', 'tank', 'gun fiend', 'bomb girl',

    # --- Jujutsu Kaisen ---
    'gojo', 'sukuna', 'nanami', 'toji', 'megumi', 'yuji',
    'nobara', 'maki', 'geto', 'yuta', 'choso', 'yuki',
    'higuruma', 'kashimo', 'hakari', 'todo', 'mei mei',
    'inume', 'kusakabe', 'panda', 'mahito', 'jogo', 'hana',
    'miwa', 'mai',
    'ito', 'shoko', 'nanako', 'mimiko', 'kento',
    'kirara', 'takaba', 'niji', 'kamo', 'naoya',
    'naobito', 'michizane', 'tengen', 'meimei', 'ui ui',

    # --- Haikyuu ---
    'niko ikki', 'alisa haiba', 'kageyama', 'hinata', 'oikawa',
    'iwaizumi', 'bokuto', 'akaashi', 'kuroo', 'kenma',
    'sugawara', 'daichi', 'asahi', 'nishinoya', 'tanaka',
    'tsukishima', 'yamaguchi', 'ushijima', 'tendou', 'sakusa',
    'atsumu', 'osamu', 'sunarin', 'kageyama', 'hinata',
    'yachi', 'shimizu', 'kinnoshita', 'onagawa', 'narita',
    'enoshita', 'misaki', 'komi', 'sarukui', 'kyoko',

    # --- One Piece ---
    'boa', 'nami', 'robin', 'yamato', 'ace', 'sabo', 'law',
    'mihawk', 'shanks', 'zoro', 'luffy', 'sanji', 'chopper',
    'usopp', 'franky', 'brook', 'jinbe', 'corazon', 'doflamingo',
    'luffy', 'kaido', 'big mom', 'shirahoshi', 'vivi',
    'reiju', 'ichiji', 'niji', 'sanji', 'yamato',
    'buggy', 'crocodile', 'moria', 'kuma', 'enel', 'lucci',
    'kaku', 'jabra', 'blueno', 'fukurou', 'kumadori',
    'oda', 'rayleigh', 'gol d roger', 'roger', 'whitebeard',
    'ace', 'sabo', 'dadan', 'koby', 'helmeppo', 'garp',
    'sengoku', 'tsuru', 'smoker', 'tashigi', 'hina',
    'fujitora', 'ryokugyu', 'aramaki', 'kizaru', 'akainu',
    'aokiji', 'kuzan', 'sakazuki', 'borsalino', 'issho',
    'perona', 'marguerite', 'sandy', 'conis', 'kaya',
    'karoo', 'laboon', 'surume', 'haredas', 'gan fall',

    # --- Hunter x Hunter ---
    'killua', 'gon', 'hisoka', 'kurapika', 'chrollo',
    'leorio', 'feitan', 'nobunaga', 'phinks', 'shizuku',
    'machi', 'paku', 'uvogin', 'kite', 'bisky', 'meruem',
    'komugi', 'netero', 'illumi', 'alluka', 'nanika',

    # --- Bleach ---
    'ichigo', 'rukia', 'renji', 'byakuya', 'toshiro', 'hitsugaya',
    'kenpachi', 'yachiru', 'aizen', 'gin', 'tosen', 'ulquiorra',
    'grimmjow', 'nel', 'halibel', 'stark', 'barragan',
    'yoruichi', 'kisuke', 'urahara', 'orihime', 'chad',
    'yhawch', 'ichibe', 'shunsui', 'yamma', 'yamamoto',
    'nanao', 'katen', 'kyoraku', 'ukitake', 'jushiro',
    'soifon', 'mayuri', 'nemu', 'zaraki', 'unohana',
    'isane', 'kensei', 'rose', 'love', 'shinji',
    'hirako', 'momo', 'rangiku', 'matsumoto', 'izuru',
    'shuhei', 'hisagi', 'ibaraki', 'komamura', 'sajin',
    'renji', 'rukia', 'toshiro', 'kaien', 'shiba',
    'kukaku', 'ganju', 'ryuken', 'isshin', 'masaki',
    'yuzu', 'karin', 'zangetsu', 'white', 'hollow ichigo',
    'aaroniero', 'szayel', 'nnoitora', 'zommari',
    'yammy', 'loly', 'menoly', 'rudbornn', 'puppy',

    # --- Naruto ---
    'naruto', 'sasuke', 'sakura', 'kakashi', 'itachi', 'shisui',
    'minato', 'kushina', 'hinata', 'gaara', 'lee', 'rock lee',
    'neiji', 'shikamaru', 'ino', 'choji', 'kiba', 'akamaru',
    'tsunade', 'jiraiya', 'orochimaru', 'obito', 'madara',
    'hashirama', 'tobirama', 'hiruzen', 'danzo', 'nairoto',
    'deidara', 'sasori', 'kakuzu', 'hidan', 'konan',
    'pain', 'nagato', 'yahiko', 'tobi', 'zetsu',
    'kabuto', 'anko', 'iruka', 'ebisu', 'gai',
    'might guy', 'kurenai', 'asuma', 'temari', 'kankuro',
    'fu', 'torune', 'shino', 'tenten', 'neji',
    'naruto', 'boruto', 'sarada', 'mitsuki', 'kawaki',
    'himawari', 'sumire', 'shin', 'kashin koji', 'jigen',
    'isshiki', 'code', 'eda', 'amon', 'deepa',

    # --- Attack on Titan ---
    'mikasa', 'levi', 'eren', 'armin', 'hange', 'erwin',
    'sasha', 'connie', 'jean', 'annie', 'reiner', 'berthold',
    'zeke', 'pieck', 'porco', 'gabi', 'falco', 'ymir',
    'historia', 'krista', 'kenny', 'freckles',
    'dina', 'grisha', 'carla', 'keith', 'shadis',
    'mike', 'nanaba', 'gelgar', 'petra', 'olou',
    'eld', 'gunter', 'nilfe', 'dot pixis', 'kitz',
    'hitch', 'marlo', 'kruger', 'owen', 'uran',

    # --- Demon Slayer ---
    'tanjiro', 'nezuko', 'zenitsu', 'inosuke', 'giyuu', 'tomioka',
    'shinobu', 'kocho', 'rengoku', 'kyojuro', 'uzui', 'tengen',
    'mitsuri', 'kanroji', 'obanai', 'iguro', 'sanemi', 'shinazugawa',
    'gyomei', 'himejima', 'muichiro', 'genya', 'kanao',
    'muzan', 'kokushibo', 'akaza', 'daki', 'gyutaro',
    'yoriichi', 'sumiyoshi', 'sakonji', 'giyuu', 'sabito',
    'makomo', 'kaigaku', 'tamayo', 'yushiro', 'chachamaru',
    'hantengu', 'sekido', 'karaku', 'aizetsu', 'zohakuten',
    'urogi', 'kaigaku', 'nakime', 'enmu', 'kyogai',
    'rui', 'spider family', 'yahaba', 'susamaru',

    # --- Kaguya-sama ---
    'kaguya', 'chika', 'miko', 'miyuki', 'ishigami', 'hayasaka',
    'ai', 'kei', 'shirogane', 'mama papa',
    'nagisa', 'karen', 'ebina', 'maki', 'tsubame',
    'kashiwagi', 'karen', 'eri', 'miyuki', 'shirogane',
    'unyo', 'ganon', 'shindou', 'oguino',

    # --- Re:Zero ---
    'rem', 'ram', 'emilia', 'beako', 'patrasche', 'felt',
    'subaru', 'natsuki subaru', 'roswaal', 'beatrice', 'echidna',
    'satella', 'petra', 'frederica', 'garfiel', 'otto',
    'priscilla', 'crusch', 'felly', 'julius',
    'typhon', 'daphne', 'carmilla', 'minerva', 'sekmet',
    'pandora', 'reinhard', 'heinkel', 'wilhelm', 'theresia',
    'regulus', 'ley', 'roy', 'stride', 'kurgan',
    'aldebaran', 'cecilus', 'halibel', 'guese', 'kan',

    # --- My Dress-Up Darling ---
    'marin', 'gojo', 'wakana', 'shion', 'nowa', 'sajuna',
    'shinju', 'amanae',
    'juju', 'suzuka', 'mizuki', 'naru', 'aoi',

    # --- Spy x Family ---
    'anya', 'yor', 'loid', 'bond', 'franky', 'beckman',
    'yuri', 'daybreak', 'nightfall', 'fiona',
    'sylvia', 'henderson', 'olka', 'martha', 'emile',
    'eben', 'mcnem', 'snidel', 'sharon', 'watson',

    # --- Oshi no Ko ---
    'ai hoshino', 'ruby', 'aqua', 'kana', 'akane', 'memcho',
    'mem', 'gotanda', 'miyako', 'taishi', 'kaburaki',
    'frill', 'melt', 'nino', 'yura', 'himekawa',
    'sumiaki', 'kami', 'abiko', 'tokyocheese', 'tesshiki',

    # --- Solo Leveling ---
    'jin woo', 'sung jinwoo', 'cha hae', 'cha haein',
    'esil', 'igris', 'baek', 'go gunhee', 'choi', 'thomas',
    'beru', 'tusk', 'knight', 'baran', 'kargalgan',
    'laura', 'joohee', 'yoo jinho', 'yoo soohyun',
    'hwang dongs', 'lim taegyu', 'gohi', 'kanae', 'shishido',
    'ryuji', 'sakamoto', 'akari', 'ssong', 'yuri', 'anna',

    # --- MHA ---
    'bakugo', 'deku', 'izuku', 'todoroki', 'shoto',
    'uraraka', 'ochaco', 'all might', 'toshinori', 'hawks',
    'dabi', 'shigaraki', 'tomura', 'aizawa', 'eraserhead',
    'midnight', 'present mic', 'endeavor', 'enji', 'mirko',
    'nejire', 'tamaki', 'mirio', 'fat gum', 'twice', 'toga',
    'shigaraki', 'all for one',
    'mineta', 'tsuyu', 'asu requiem', 'ibo', 'reiko',
    'setsuna', 'manga', 'sen kaibara', 'shishida', 'rin',
    'kosei', 'hiryu', 'this', 'everywhere', 'garvey',
    'star and stripe', 'stain', 'nagant', 'overhaul',
    'kurogiri', 'nomu', 'high end', 'gigantomachia', 'skeptic',
    'trumpet', 'spinner', 'magne', 'compress', 'mustang',
    're destro', 'kuno', 'captain celebrity',

    # --- Evangelion ---
    'asuka', 'rei', 'shinji', 'misato', 'kaworu', 'ritsuko',
    'gendo', 'yui', 'pen pen', 'mari',
    'toji', 'kensuke', 'hikari', 'rilve', 'naoko',
    'keel', 'kozou', 'makoto', 'shigeru', 'maya',

    # --- Kimi no Nawa / Your Name ---
    'mitsuha', 'taki', 'mikipon', 'okudera', 'teshi',

    # --- Bocchi the Rock ---
    'bocchi', 'ryo', 'nijika', 'kita', 'ikuyo', 'yamada',
    'hitori', 'gotoh',
    'pa san', 'seika', 'futari', 'kikuri', 'eli',

    # --- Frieren ---
    'frieren', 'fern', 'stark', 'ube', 'ubel', 'land', 'wirbel',
    'denken', 'methode', 'genau', 'sense', 'sein', 'hero heiter',
    'kraft', 'himmel', 'heiter', 'eisen', 'flamme', 'serie',
    'linie', 'lugner', 'draht', 'revolte', 'solitar',

    # --- Mushoku Tensei ---
    'roxy', 'eris', 'ghislaine', 'sylphy', 'sylphiette',
    'rudy', 'rudeus', 'paul', 'zenith', 'lilia', 'orsted',
    'ruijerd', 'kishirika', 'fitts',
    'elinalise', 'talhand', 'soldat', 'norn', 'aysha',
    'hitogami', 'nanahoshi', 'perugius', 'pixis', 'darius',

    # --- Dandadan ---
    'momo', 'okarun', 'seiko', 'ayase', 'takakura', 'ken',
    'aera', 'jia', 'granny seiko', 'turbo granny',
    'serpo', 'acrobatic silly', 'evil eye',
    'vamola', 'ukupan', 'sakata', 'count saint germain',
    'danman', 'maku', 'peeny', 'pennywise', 'dover demon',

    # --- Vocaloid ---
    'miku', 'hatsune miku', 'rin', 'kagamine rin', 'len',
    'kagamine len', 'luka', 'megurine luka', 'gumi', 'megpoid',
    'tet', 'kaito', 'meiko', 'des', 'piko', 'yuki kaai',
    'mayu', 'oriki', 'una', 'otona', 'sekaai',
    'cocol', 'koyka', 'akiko', 'uno', 'chika',

    # --- Touhou ---
    'reimu', 'marisa', 'cirno', 'flandre', 'sakuya',
    'remilia', 'patchouli', 'yukari', 'youmu', 'yuyuko',
    'sanae', 'suwako', 'kanako', 'alice', 'aya', 'chen',
    'lily white', 'ran', 'koishi', 'satori', 'orin',
    'okuu', 'tenshi', 'miko', 'byakuren', 'suika',
    'iku', 'hatate', 'momiji',
    'toyosatomimi no miko', 'wakasagihime', 'sekibanki',
    'daiyousei', 'kisume', 'yamame', 'nitori', 'kogasa',
    'saka', 'seija', 'shinmyoumaru', 'hecatia', 'clownpiece',
    'juni', 'sagume', 'okina', 'mima', 'eli', 'yumemi',

    # --- Original Characters ---
    'oc', 'ori char', 'original character', 'ocs',

    # --- K-Pop Idols (often sold as merch) ---
    'heeseung', 'jake', 'jay', 'sunghoon', 'jungwon', 'ni-ki',
    'niki', 'beomgyu', 'soobin', 'yeonjun', 'taehyun', 'huening',
    'huening kai', 'bang chan', 'changbin', 'han', 'felix',
    'seungmin', 'hyunjin', 'jin', 'suga', 'jhope', 'rm',
    'jimin', 'v', 'jungkook', 'karina', 'winter', 'giselle',
    'ningning', 'irene', 'seulgi', 'joy', 'yeri',
    'rose', 'jennie', 'lisa', 'jisoo',
    'chaeyoung', 'dahyun', 'tzuyu', 'nayeon', 'jihyo',
    'sana', 'momo', 'mina', 'chaewon', 'sakura',
    'yunjin', 'kazuha', 'eunchae', 'yujin', 'wonyoung',
    'rei', 'leeseo', 'liz', 'gaeul', 'wonjung',
    'jiwoo', 'kyujin', 'yunah', 'minju', 'iroha',
    'moka', 'wonhee', 'youngseo', 'yeju', 'sohyun',
    'natty', 'sullin', 'taiyaki', 'ayaka', 'riku',
    'kokoro', 'mary', 'yuha', 'nana', 'leejung',
    'dowha', 'dennis', 'jesse', 'huh', 'taki',

    # --- FF / Square Enix ---
    'noctis', 'lunafreya', 'prompto', 'ignis', 'gladiolus',
    'tifa', 'aerith', 'cloud', 'sephiroth', 'squall',
    'rinoa', 'zidane', 'garnet', 'tidus', 'yuna',
    'lulu', 'rikku', 'lightning', 'serah', 'terra',
    'celes', 'edgar', 'sabin', 'kain', 'cid',
    'sora', 'riku', 'kairi', 'roxas', 'xehanort',
    'aqua', 'terra', 'ven', 'ventus', 'axel',
    'lea', 'xion', 'namin', 'mickey', 'donald',
    'goofy', 'cloud strife', 'barret', 'red xiii',
    'nanaki', 'yuffie', 'cait sith', 'zack', 'shae',
    'sazh', 'vanille', 'hope', 'fro', 'balthier',
    'basch', 'ashe', 'vann', 'penelo', 'larsa',
    'yang', 'emanor', 'garnet', 'ivy', 'serge',

    # --- Other games / series ---
    'sonic', 'tails', 'knuckles', 'amy', 'shadow',
    'mario', 'luigi', 'peach', 'daisy', 'yoshi',
    'link', 'zelda', 'ganon', 'mipha', 'urbosa',
    'revali', 'daruk', 'samus', 'kraid', 'ridley',
    'traveler', 'kaeya', 'lisa', 'fischl', 'amber',
    'diluc', 'jean', 'keqing', 'qiqi', 'mona',
    'venti', 'zhongli', 'raiden mei', 'nahida',
    'furina de fontaine', 'navia caspar', 'nilou',
    'albedo', 'sucrose', 'noelle', 'gorou',
    'itto', 'ayato', 'shinobu', 'heizou',
    'ratchet', 'clank', 'crash bandicoot', 'spyro',
    'master chief', 'cortana', 'doomguy', 'kratos',
    'atria', 'ken', 'alucard', 'dante', 'nero',
    '2b', '9s', 'a2', 'joker', 'selene', 'diablo',

    # --- Bungo Stray Dogs ---
    'dazai', 'chuuya', 'atsushi', 'akutagawa', 'fukuzawa',
    'mori', 'yokomizo', 'tanizaki', 'kenji', 'higuchi',
    'odasaku', 'fitzgerald', 'lovecraft', 'nikolai',
    'sigma', 'gogol', 'pushkin', 'fukushi',
    'kyoka', 'yokito', 'no longer', 'yosano', 'ranpo',
    'kyuusaku', 'michizou', 'poe', 'lucy', 'montgomery',
    'mitchell', 'freeman', 'chapman', 'howard', 'holmes',
    'bram', 'aqutuage', 'teruko', 'jouno', 'tecchou',

    # --- Persona ---
    'joker', 'ren amamiya', 'morgana', 'ryuji', 'ann',
    'yusuke', 'makoto', 'futaba', 'haru', 'sumire',
    'akechi', 'maruki', 'lavenza', 'igor', 'sojiro',
    'yu', 'yosuke', 'chie', 'kanji', 'naoto',
    'rise', 'teddie', 'nanako', 'adachi', 'dojima',
    'minato', 'yukari', 'junpei', 'akechi', 'mitsuru',
    'akihiko', 'fuuka', 'koromaru', 'shinji', 'ken',
    'elizabeth', 'margaret', 'theodore', 'caroline',
    'justine', 'jos', 'kashiwagi', 'oni', 'iwai',

    # --- Mobile Legends ---
    'ling', 'lance', 'claude', 'hayabusa', 'fanny',
    'gusion', 'lancelot', 'selena', 'karina', 'lilia',
    'lesley', 'beatrix', 'natan', 'brody', 'granger',
    'chang e', 'lunox', 'guinevere', 'odette',
    'vale', 'xavier', 'yve', 'pharsa', 'valir',
    'akai', 'barats', 'jawhead', 'khufra', 'tigreal',
    'franco', 'chou', 'paquito', 'silvanna', 'esmeralda',
    'joy', 'novaria', 'arlot', 'khaleed', 'dyrroth',
    'terizla', 'alduous', 'martis', 'thamuz', 'masha',
    'grock', 'lolita', 'gloo', 'belerick', 'minotaur',
    'angela', 'rafaela', 'estes', 'floryn', 'mathilda',
    'kaja', 'natalia', 'saber', 'alucard', 'zilong',

    # --- Valorant (characters) ---
    'jett', 'phoenix', 'reyna', 'raze', 'sage',
    'viper', 'omen', 'breach', 'brim', 'killjoy',
    'cypher', 'kayo', 'skye', 'yoru', 'astra',
    'neon', 'chamber', 'fade', 'harbor', 'gekko',
    'deadlock', 'iso', 'clove', 'vyse', 'tejo',
    'waylay',

    # --- Sanrio ---
    'cinnamoroll', 'kuromi', 'my melody', 'pompompurin',
    'pochaco', 'hello kitty', 'gudetama', 'aggretsuko',
    'badtz maru', 'keroppi', 'chococat',
    'hangyodon', 'pekpek', 'chibimaru', 'little twin',
    'minna no tabo', 'sugbunnies', 'sweetino', 'tuxedo',

    # --- Pokemon ---
    'eevee', 'pikachu', 'charizard', 'gengar', 'umbreon',
    'espeon', 'sylveon', 'mew', 'mimikyu', 'jolteon',
    'flareon', 'vaporeon', 'leafeon', 'glaceon', 'rayquaza',
    'mewtwo', 'lugia', 'ho-oh', 'celebi', 'jirachi',
    'arceus', 'dialga', 'palkia', 'giratina',
    'sprigatito', 'fuecoco', 'quaxly', 'pawmi',
    'appletun', 'dragonite', 'gyarados', 'gardevoir',
    'lucario', 'greninja', 'charizard',
    'ditto', 'magikarp', 'squirtle', 'bulbasaur', 'charmander',
    'mudkip', 'treecko', 'torchic', 'piplup', 'turtwig',
    'chimchar', 'snivy', 'tepig', 'oshawott', 'froakie',
    'fennekin', 'chespin', 'rowlet', 'litten', 'popplio',
    'grookey', 'scorbunny', 'soble', 'wooper', 'snorlax',

    # --- Love Live ---
    'honoka', 'eli', 'kotori', 'umi', 'rin', 'maki',
    'hanayo', 'nico', 'nozomi', 'chika', 'you', 'rikko',
    'kanan', 'diae', 'yoshiko', 'yohane', 'mari', 'ruby',
    'kanon', 'keke', 'hii', 'shiki', 'natsumi', 'sayuri',
    'chisato', 'sumire', 'ren', 'megumi', 'lanzhu', 'miasha',
    'kaho', 'kinako', 'mei', 'shiki', 'ayaka', 'maai',
    'hasu no sora', 'snow halation', 'mermaid festa',

    # --- Uma Musume ---
    'special week', 'silence suzuka', 'tokai teio', 'mejiro mcdowell',
    'oguri cap', 'kitasan black', 'satono diamond', 'vodka',
    'taiki shave', 'grass wonder', 'bakushin o', 'maruzensky',
    'el condor pasa', 't manage', 'super creek', 'nice nature',
    'urara', 'tamamo cross', 'manhattan cafe', 'hishi amazon',
    'mayano top', 'air grove', 'biwa hayate', 'eishin flash',
    'narita brian', 'winning ticket', 'rice shower', 'yamanin zephyr',
    'agnes tachyon', 'seeking the gold', 'daitaku helios',
    'inari one', 'sakura bakushin', 'mihono bourbon',

    # --- BanG Dream / Project Sekai ---
    'kasumi', 'arisa', 'saaya', 'tai', 'rimi',
    'kokoro', 'kaoru', 'hagumi', 'misaki', 'michelle',
    'rani', 'moca', 'himari', 'tomoe', 'tsugumi',
    'aya', 'hina', 'chisato', 'maya', 'eve',
    'yukina', 'sayo', 'lisa', 'ako', 'rinko',
    'masuki', 'chiyu', 'mashiro', 'touko', 'nanami',
    'hina', 'nagisa', 'tsukushi', 'haroharo', 'niji yo',
    'ichika', 'saki', 'honami', 'shiho', 'miku',
    'minori', 'haruka', 'airi', 'shizuku', 'kohane',
    'an', 'akito', 'toya', 'tsukasa', 'emu',
    'nene', 'rui', 'marina', 'meiko', 'kaito', 'len',

    # --- Azur Lane ---
    'enterprise', 'belfast', 'akagi', 'kaga', 'nagato',
    'hood', 'prince of wales', 'warspite', 'queen elizabeth',
    'takao', 'atago', 'aya', 'shokaku', 'zuikaku',
    'yorktown', 'hornet', 'souryuu', 'hiryuu', 'ajax',
    'edinburgh', 'sirius', 'sheffield', 'newcastle',
    'bismarck', 'tirpitz', 'prinz eugen', 'hipper',
    'roon', 'friedrich', 'friedrich der grose',
    'sovetskaya', 'belorussiya', 'suzuya', 'kumado',
    'sango', 'shimakaze', 'yuudachi', 'poi', 'fubuki',
    'torino', 'venezia', 'rivioli', 'u 47', 'komomoe',
    'laffey', 'z23', 'javelin', 'ayanami', 'unicon',
    'chang chun', 'tai yuan', 'an shan', 'fu shun', 'ning hai',
    'ping hai', 'yat sen', 'pet pee', 'york', 'exeter',

    # --- Girls Frontline ---
    'm4a1', 'sopmod', 'm16a1', 'st ar15', 'hkm4',
    'gr g41', 'hk416', 'sr 3mp', 'aug', 'type 95',
    'wa2000', 'sv98', 'svd', 'dsr 50', 'ntw 20',
    'sat8', 'hk21', 'pkp', 'mg5', 'negev',
    'uzi', 'vector', 'p90', 'sten', 'mp5',
    'g36', 'scout', 'ak 47', 'as val', 'kar98',
    'springfield', 'm1911', 'calico', 'carcano',
    'dmr', 'jill', 'lenna', 'mika', 'alma', 'angie',
    'groza', 'aek', 'an 94', 'rpk 74', 'rfb',

    # --- Granblue Fantasy ---
    'gran', 'djeeta', 'lyria', 'vyrn', 'katalina',
    'rackam', 'io', 'eugene', 'rosetta', 'sierokarte',
    'narmaya', 'percival', 'siegfried', 'beatrix',
    'zooey', 'andira', 'anila', 'mahira', 'vajra',
    'khumbira', 'rat', 'boar', 'dog', 'monkey',
    'sandolphon', 'lucio', 'lucifer', 'belial',
    'sandalphon', 'shalem', 'ladiva', 'sophia',
    'vikala', 'charlotta', 'saram', 'cagliostro',
    'fiorito', 'yaia', 'mirin', 'aliza', 'luisee',
    'sutera', 'misen', 'medusa', 'artemis', 'apollo',
    'orchid', 'mora', 'elmel', 'jesuis', 'keni',
    'samsara', 'hatsune miku', 'makura', 'kamen',

    # --- Princess Connect Re:Dive ---
    'pecorine', 'kokkoro', 'karyl', 'saren',
    'mitsuki', 'akari', 'yuuki', 'suzuna', 'ilya',
    'eriko', 'shinobu', 'labyrista', 'muimi',
    'neneka', 'christina', 'nozomi', 'tomo',
    'shizuru', 'rin', 'yui', 'rei', 'hiyori',
    'hatsune', 'shiori', 'kyaru', 'maho', 'makoto',
    'kaori', 'mio', 'misogi', 'kyouka', 'tamaki',
    'mifuyu', 'yuki', 'ayane', 'kurumi', 'misato',
    'suzume', 'rima', 'chloe', 'chieru', 'yuni',

    # --- Idolmaster ---
    'haruka', 'chihaya', 'miki', 'yukiho', 'makoto',
    'iori', 'takane', 'ritsuko', 'azusa', 'iori',
    'yayoi', 'ami', 'mami', 'hibiki', 'jupiter',
    'mirai', 'shizuka', 'tsubasa', 'kana', 'kotoha',
    'elena', 'rei', 'emi', 'anastasia', 'hoshii',
    'chloe', 'alina', 'yuriko', 'kirinko', 'nanami',
    'momoko', 'rinze', 'natsuha', 'asahi', 'fuka',
    'kogane', 'kumada', 'ichinose', 'tenkawa',

    # --- SAO ---
    'kirito', 'asuna', 'sinon', 'leafa', 'yuuki',
    'alice', 'eugeo', 'kayaba', 'yui', 'klein',
    'agil', 'silica', 'lizbet', 'liz', 'sachi',
    'heathcliff', 'sugou', 'quinella', 'admins',
    'cardinal', 'berculi', 'fanatio', 'dew',
    'liena', 'ronye', 'tiese', 'selka', 'sortiliena',
    'medina', 'raynos', 'saito', 'shino', 'kuradeel',

    # --- Konosuba ---
    'kazuma', 'aqua', 'megumin', 'darkness', 'lalatin',
    'yun yun', 'wiz', 'vanir', 'eiris', 'beldia',
    'dust', 'luna', 'mitsurugi', 'sylvia', 'cecilia',
    'sena', 'yui yui', 'suke', 'eida', 'wolf',

    # --- Code Geass ---
    'lelouch', 'suzaku', 'c2', 'cc', 'kallen',
    'nunally', 'euphemia', 'cornelia', 'schneizel',
    'lloyd', 'cecil', 'viletta', 'ohgi', 'tamaki',
    'sayoko', 'milly', 'roro', 'jeremiah', 'orange',
    'gino', 'ankya', 'monica', 'bianca', 'sherry',
    'marianne', 'charles', 'v2', 'sasuke', 'kaguya',

    # --- Steins;Gate ---
    'okabe', 'kurisu', 'mayuri', 'daru', 'moeka',
    'luko', 'faris', 'suzuha', 'kagari', 'yuki',
    'reina', 'nakase', 'brian', 'tina', 'chris',

    # --- Reincarnated Slime ---
    'rimuru', 'milim', 'benimaru', 'shuna', 'shion',
    'diablo', 'guy crimson', 'ramiris', 'veldora',
    'velgrynd', 'chloe', 'hinata', 'kagali', 'ramen',
    'gobta', 'soei', 'hakuro', 'geld', 'gabiru',
    'violet', 'testarossa', 'ultima', 'carilon',
    'mizuley', 'adellman', 'jester', 'smokey',

    # --- DanMachi ---
    'bell', 'aiz', 'hestia', 'lili', 'ryu',
    'eina', 'freya', 'syr', 'haruhime', 'ais',
    'tione', 'tiona', 'lefiya', 'fin', 'gareth',
    'asfi', 'revis', 'ottar', 'allen', 'gulliver',
    'mama mia', 'mikoto', 'welf', 'takemikazuchi',

    # --- Overlord ---
    'ainz', 'albedo', 'shalltear', 'demiurge', 'coctyus',
    'victim', 'gargantua', 'rubedo', 'nberra',
    'pandora actor', 'mare', 'aura', 'zessy',
    'entoma', 'solution', 'sebas', 'shizu', 'yuri alpha',
    'cz delta', 'lupusregina', 'narberal', 'alpha',
    'clementine', 'brain', 'go gin', 'zero', 'hair', 'catsu',

    # --- Tokyo Revengers ---
    'takemichi', 'mikey', 'draven', 'ken', 'chifuyu',
    'baji', 'kisaki', 'kazu', 'yuzuha', 'senju',
    'south', 'kakugo', 'hamazono', 'shin', 'waka',
    'benkei', 'mucho', 'p hel', 'smiley', 'angry',
    'pah chin', 'masaki', 'naoto', 'hina', 'emma',

    # --- Classroom of the Elite ---
    'kiyataki', 'honami', 'suzune', 'kei', 'sakurako',
    'mao', 'sato', 'kushida', 'ichinose', 'ryuuen',
    'koenji', 'hirata', 'sudoh', 'sae', 'chabashira',
    'hoshinomiya', 'hashimoto', 'hasebe', 'matsu', 'ike',
    'yukimura', 'sudo', 'keleo', 'masumi', 'airi',

    # --- Wind Breaker ---
    'haruka sakura', 'hayato sugi', 'kyora umemiya',
    'taiki togame', 'jo togame', 'enna hiragi',
    'nirei akihiko', 'kotoha sugi', 'suzuri',
    'kaji ren', 'tsugeura', 'matsumoto', 'kinjo',
    'banjo', 'arima', 'yatomi', 'nagayama',

    # --- Kaiju No 8 ---
    'kafka', 'reno', 'mina', 'hoshina', 'soshiro',
    'haruichi', 'kikoru', 'narumi', 'geno', 'okonogi',
    'asa', 'shed', 'frass', 'ishihara', 'shimada',
    'himura', 'ikebe', 'fukushin', 'bakko', 'kaiju no 8',

    # --- Sakamoto Days ---
    'taro sakamoto', 'shin', 'lu', 'aoi', 'hana',
    'nagumo', 'fat sakamoto', 'kindaka', 'boiled',
    'obiguro', 'kashima', 'osaragi', 'takamura',
    'kamihate', 'tanabata', 'tokeshi', 'mankai',
    'yonaga', 'umekawa', 'shinra', 'zaha', 'akane',
    'janitor', 'matsushima', 'shinichiro',

    # --- Dungeon Meshi ---
    'laios', 'marcille', 'chilchuck', 'senshi',
    'falin', 'izutsumi', 'namari', 'shuro', 'toshiro',
    'marciste', 'kikki', 'malkin', 'fleki', 'holms',
    'michelle', 'thistle', 'lycion', 'dylan',
    'seir', 'adventurer', 'griffon', 'kitsuna',
    'patti', 'ranger', 'dast', 'baba', 'dullah',

    # --- Vinland Saga ---
    'thorfin', 'askeladd', 'canute', 'einari',
    'thorkell', 'thors', 'helga', 'yiu', 'torgrim',
    'gudrid', 'leif', 'halfdan', 'sven', 'floki',
    'ketil', 'pater', 'arnheid', 'gardar', 'swan',
    'hild', 'stig', 'stork', 'thorgil', 'narr', 'hall',

    # --- Cyberpunk Edgerunners ---
    'david', 'lucy', 'kiwi', 'maine', 'doriot',
    'rebecca', 'pilar', 'farewell', 'adamo',
    'falco', 'tokyo', 'katsuo', 'tanaka', 'norris',
    'adam smasher', 'smacker', 'smasher', 'lizzie',

    # --- 86 ---
    'shin', 'lena', 'vladilena', 'kurena', 'raiden',
    'theo', 'kaie', 'daiya', 'haruto', 'anju',
    'sasha', 'olivia', 'noct', 'sana', 'cyril',

    # --- Violet Evergarden ---
    'violet', 'gilbert', 'hodgins', 'cattleya',
    'erica', 'iris', 'claudia', 'benedict', 'dietfried',
    'oscar', 'kyon', 'shere', 'lucca', 'almira',
    'alex', 'verona', 'kihana', 'veronica', 'luca',

    # --- Lycoris Recoil ---
    'chisato', 'takina', 'mizuki', 'kurumi', 'mika',
    'yoshi', 'himegama', 'shinji', 'reiki', 'majima',
    'robota', 'whisper', 'tactical', 'alpha', 'gemini',

    # --- Toaru / Index / Railgun ---
    'index', 'touma', 'misaka', 'mikoto', 'kuroko',
    'shirai', 'kaori', 'seiri', 'fukiyose', 'itsumi',
    'maika', 'frenda', 'mugino', 'shizuri', 'rukuro',
    'accelerator', 'last order', 'worst', 'kakine',
    'hamazura', 'takitsubo', 'kinuhata', 'toriyama',
    'oriyana', 'saten', 'uiharu', 'kiharazi',

    # --- A Certain Magical Index -- covered above
}

CHARACTER_ALIASES = {
    'niko ikki': 'Niko Ikki (Haikyuu)',
    'alisa haiba': 'Alisa Haiba (Haikyuu)',
    'castoria': 'Castoria (Fate)',
    'calliope': 'Calliope (Hololive)',
    'gojo': 'Gojo (JJK)',
    'nanami': 'Nanami (JJK)',
    'sukuna': 'Sukuna (JJK)',
    'kobo': 'Kobo Kanaeru (Hololive ID)',
    'anya melfissa': 'Anya Melfissa (Hololive ID)',
    'peko': 'Pekora (Hololive)',
    'marine': 'Marine (Hololive)',
    'rem': 'Rem (Re:Zero)',
    'ram': 'Ram (Re:Zero)',
    'emilia': 'Emilia (Re:Zero)',
    'frieren': 'Frieren (Sousou no Frieren)',
    'bocchi': 'Bocchi (Bocchi the Rock)',
    'ai hoshino': 'Ai Hoshino (Oshi no Ko)',
    'marin': 'Marin Kitagawa (Sono Bisque Doll)',
    'kaguya': 'Kaguya (Kaguya-sama)',
    'miku': 'Hatsune Miku (Vocaloid)',
    'asuka': 'Asuka (Evangelion)',
}


def load_data():
    if not os.path.isfile(CSV_PATH):
        print(f"File {CSV_PATH} tidak ditemukan")
        sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    df['full_text'] = df['full_text'].fillna('').astype(str)
    return df


def find_iso_tweets(df):
    mask = df['full_text'].str.contains(ISO_PATTERNS, na=False)
    return df[mask].copy()


def classify_urgency(text):
    t = text.lower()
    score = 0
    for word, val in URGENCY_WORDS.items():
        if word in t:
            score += val
    if score >= 3:
        return 'Desperate', score
    elif score >= 1:
        return 'Normal', score
    return 'Santai', 0


def analyze_character_urgency(df_iso, all_found_counter, user_keywords=None):
    char_data = {}
    for _, row in df_iso.iterrows():
        text = row['full_text']
        label, score = classify_urgency(text)
        chars = extract_characters(text, user_keywords)
        for c in chars:
            if c not in char_data:
                char_data[c] = {'total': 0, 'desperate': 0, 'score_sum': 0}
            char_data[c]['total'] += 1
            char_data[c]['score_sum'] += score
            if label == 'Desperate':
                char_data[c]['desperate'] += 1
    return char_data


SERIES_HINT = re.compile(r'\b(genshin|hsr|star rail|honkai|zzz|zenless|nikke|fate|arknights|blue archive|hololive|chainsaw man|jjk|jujutsu|haikyuu|one piece|hxh|hunter|bleach|naruto|aot|demon slayer|kny|mha|my hero|re:zero|kaguya|oshi no ko|spy family|evangelion|touhou|vocaloid|pokémon|solo leveling|mlbb|mobile legends|valorant|persona|bungo|dandadan|frieren|mushoku|chainsaw|dsmp)\b', re.IGNORECASE)

SERIES_KEYWORDS = {
    'genshin', 'genshin impact', 'hsr', 'honkai star rail', 'star rail', 'honkai',
    'zzz', 'zenless', 'zenless zone zero', 'nikke', 'fate', 'fate grand order', 'fgo',
    'arknights', 'blue archive', 'hololive', 'chainsaw man', 'csm',
    'jjk', 'jujutsu kaisen', 'jujutsu', 'haikyuu', 'one piece',
    'hxh', 'hunter hunter', 'hunter x hunter', 'bleach',
    'naruto', 'naruto shippuden', 'aot', 'attack on titan', 'shingeki',
    'demon slayer', 'kimetsu', 'kny', 'mha', 'my hero academia', 'boku no hero',
    're:zero', 're zero', 'kaguya sama', 'kaguya', 'love is war',
    'oshi no ko', 'spy family', 'spyxfamily',
    'evangelion', 'eva', 'touhou', 'vocaloid', 'pokemon', 'pokémon', 'pokemon',
    'solo leveling', 'mlbb', 'mobile legends', 'valorant',
    'persona', 'bungo stray dogs', 'bsd', 'dandadan',
    'frieren', 'mushoku tensei', 'chainsaw man', 'csm',
    'love live', 'lovelive', 'umamusume', 'uma musume',
    'bang dream', 'bangdream', 'project sekai', 'proseka',
    'azur lane', 'girls frontline', 'granblue', 'granblue fantasy',
    'gbft', 'princess connect', 'priconne', 'idolmaster', 'imas',
    'sao', 'sword art online', 'konosuba', 'code geass',
    'steins gate', 'steins;gate', 'tensura', 'reincarnated slime',
    'danmachi', 'dan machi', 'overlord', 'tokyo revengers',
    'toure', 'classroom of the elite', 'youzitsu',
    'wind breaker', 'kaiju no 8', 'sakamoto days',
    'dungeon meshi', 'vinland saga', 'edgerunners',
    'cyberpunk', 'lycoris recoil', 'violet evergarden',
    'kny', 'kimetsu no yaiba', 'mha', 'boku no hero',
    'aot', 'shingeki no kyojin', 'hxh', 'hunter x hunter',
    'jjk', 'jujutsu kaisen', 'csm', 'chainsaw man',
}


def extract_characters(text, user_keywords=None):
    found = set()
    text_lower = text.lower()
    iso_match = ISO_PATTERNS.search(text)

    if not iso_match:
        return []

    iso_pos = iso_match.end()
    context_after = text[iso_pos:iso_pos + 200].strip()
    context_before = text[max(0, iso_pos - 100):iso_pos].strip()

    # Pattern 1: known characters anywhere in the text (with word boundary for short names)
    _known = list(KNOWN_CHARACTERS)
    if user_keywords:
        _known.extend(user_keywords)
    for char in _known:
        if not char or len(char) < 2:
            continue
        if len(char) <= 5 and ' ' not in char:
            if re.search(r'\b' + re.escape(char) + r'\b', text_lower):
                resolved = CHARACTER_ALIASES.get(char, char.title())
                found.add(resolved)
        else:
            if char in text_lower:
                resolved = CHARACTER_ALIASES.get(char, char.title())
                found.add(resolved)

    # Pattern 2: "esp [name]" or "especially [name]" — strong signal
    for esp_match in re.finditer(r'\besp\b\s+([A-Z]\w+(?:\s+[A-Z]\w+)?)', text[iso_pos:iso_pos + 200]):
        name = esp_match.group(1)
        found.add(name)

    # Pattern 3: names in series-specific patterns
    # "merch [name]" or "[name] genshin/hsr/etc"
    series_matches = set()
    for m in SERIES_HINT.finditer(text_lower):
        series = m.group(1)
        # Get words before the series name
        before = text_lower[:m.start()].strip()
        before_words = before.split()[-5:] if before else []
        for bw in before_words:
            if bw[0].isupper() and len(bw) > 2:
                series_matches.add(bw)
        # Get words after the series name
        after = text_lower[m.end():].strip()
        after_words = after.split()[:5] if after else []
        for aw in after_words:
            if aw[0].isupper() and len(aw) > 2:
                series_matches.add(aw)

    for name in series_matches:
        nl = name.lower()
        if nl in NOISE_WORDS or nl in SERIES_KEYWORDS:
            continue
        if nl in KNOWN_CHARACTERS:
            resolved = CHARACTER_ALIASES.get(nl, name)
            found.add(resolved)
        elif len(name) >= 4:
            found.add(name)

    # Pattern 4: capitalized words after ISO keyword — ONLY if known char or multi-word
    # Single words
    caps_after = re.findall(r"[A-Z]\w+", context_after)
    for word in caps_after:
        w = word.lower()
        if w in KNOWN_CHARACTERS:
            resolved = CHARACTER_ALIASES.get(w, word)
            found.add(resolved)
        elif 4 <= len(word) <= 15 and not w.startswith('http'):
            # Check if followed by a series name
            after_idx = context_after.lower().find(word.lower()) + len(word)
            after_text = context_after[after_idx:after_idx + 40].lower()
            for series in SERIES_KEYWORDS:
                if series in after_text:
                    found.add(word)
                    break

    # Pattern 5: multi-word proper names
    multi = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', context_after)
    for name in multi:
        w = name.lower()
        if any(w.startswith(nw) for nw in {'comifuro', 'comic', 'frontier', 'please', 'looking', 'jakarta', 'bandung', 'surabaya'}):
            continue
        parts = w.split()
        if any(p in KNOWN_CHARACTERS for p in parts):
            found.add(name)
        elif 6 <= len(name) <= 30:
            found.add(name)

    # Pattern 6: text in quotes after ISO keyword
    quoted = re.findall(r"[""''""](.+?)[""''""]", context_after)
    for q in quoted:
        q = q.strip()
        if not (3 <= len(q) <= 40) or q.lower().startswith('http'):
            continue
        ql = q.lower()
        if ql in NOISE_WORDS or ql in SERIES_KEYWORDS:
            continue
        if ql in KNOWN_CHARACTERS:
            resolved = CHARACTER_ALIASES.get(ql, q.title())
            found.add(resolved)
        elif re.search(r'[A-Z]', q):
            found.add(q.title())

    # Pattern 7: names in list after ISO keyword (e.g., "- name - name" or "name, name")
    list_items = re.findall(r'[-–•]\s*([A-Z][a-zA-Z]+)', context_after)
    for item in list_items:
        w = item.lower()
        if w in KNOWN_CHARACTERS:
            resolved = CHARACTER_ALIASES.get(w, item)
            found.add(resolved)

    # Pattern 8: parenthesized text after ISO keyword (e.g., "wtb (nama char)")
    parenthesized = re.findall(r'\(([^)]+)\)', context_after)
    for p in parenthesized:
        p = p.strip()
        if not (3 <= len(p) <= 40) or p.lower().startswith('http'):
            continue
        pl = p.lower()
        if pl in NOISE_WORDS or pl in SERIES_KEYWORDS:
            continue
        if pl in KNOWN_CHARACTERS:
            resolved = CHARACTER_ALIASES.get(pl, p.title())
            found.add(resolved)
        elif re.search(r'[A-Z]', p):
            words = p.split()
            if not any(w.lower() in NOISE_WORDS for w in words):
                found.add(p)
        else:
            for w in re.findall(r'[A-Za-z]{3,}', p):
                wl = w.lower()
                if wl in KNOWN_CHARACTERS:
                    resolved = CHARACTER_ALIASES.get(wl, w.title())
                    found.add(resolved)

    # Pattern 9: any capitalized word from before the ISO keyword too
    for word in re.findall(r"[A-Z]\w{2,}", context_before):
        w = word.lower()
        if w in KNOWN_CHARACTERS and w not in NOISE_WORDS and w not in SERIES_KEYWORDS:
            resolved = CHARACTER_ALIASES.get(w, word)
            found.add(resolved)

    # Pattern 10: lowercase words near ISO keyword (very conservative — only known chars)
    for word in re.findall(r'\b([a-z]{4,})\b', context_after[:70]):
        wl = word.lower()
        if wl not in KNOWN_CHARACTERS:
            continue
        if wl in NOISE_WORDS or wl in SERIES_KEYWORDS:
            continue
        resolved = CHARACTER_ALIASES.get(wl, word.title())
        found.add(resolved)

    # Pattern 11: long lowercase words (7+ chars) near ISO keyword as potential character name
    for word in re.findall(r'\b([a-z]{7,})\b', context_after[:70]):
        wl = word.lower()
        if wl in NOISE_WORDS or wl in SERIES_KEYWORDS or wl in KNOWN_CHARACTERS:
            continue
        if any(tld in wl for tld in {'com', 'co', 'id', 'net', 'org'}):
            continue
        if wl in {
            'looking', 'please', 'found', 'check', 'price', 'offer', 'trade', 'direct',
            'message', 'interest', 'condition', 'original', 'sealed', 'brand', 'listed',
            'collection', 'include', 'bundle', 'combo', 'package', 'product', 'status',
            'update', 'comment', 'bought', 'sold', 'open', 'close', 'contact', 'seller',
            'buyer', 'payment', 'shipping', 'express', 'regular', 'economy', 'tracking',
            'invoice', 'receipt', 'warranty', 'exchange', 'refund', 'return', 'cancel',
            'deposit', 'transfer', 'order', 'reserve', 'request', 'inquiry', 'question',
            'available', 'ready', 'stock', 'preorder', 'limited', 'exclusive', 'special',
            'discount', 'promo', 'voucher', 'coupon', 'freebie', 'bonus', 'extra',
            'urgent', 'important', 'serious', 'sincere', 'genuine', 'legit', 'trusted',
            'guarantee', 'quality', 'mint', 'perfect', 'excellent', 'good', 'great',
            'nice', 'beautiful', 'cute', 'adorable', 'lovely', 'pretty', 'cool', 'awesome',
            'amazing', 'fantastic', 'wonderful', 'splendid', 'gorgeous', 'stunning',
            'interested', 'interested', 'sembarang', 'barang', 'semua', 'lain', 'lainnya',
            'tweet', 'reply', 'thread', 'retweet', 'quote', 'share', 'like', 'follow',
            'mention', 'notification', 'alert', 'reminder', 'deadline', 'bump',
            'semoga', 'moga', 'mudah', 'cepat', 'laku', 'terjual', 'dibeli',
            'masih', 'setelah', 'sebelum', 'besok', 'kemarin', 'nanti', 'tadi',
            'semua', 'beberapa', 'sendiri', 'bersama', 'tentang', 'antara',
            'melalui', 'karena', 'tetapi', 'namun', 'sedangkan', 'sementara',
            'sehingga', 'mengenai', 'menurut', 'kepada', 'dengan', 'untuk',
            'dapat', 'harus', 'boleh', 'mungkin', 'sekitar', 'kurang', 'lebih',
            'paling', 'sangat', 'sekali', 'terlalu', 'sedang', 'pernah', 'bukan',
            'tidak', 'selalu', 'jarang', 'sering', 'kadang', 'sekarang',
            'baru', 'lama', 'cepat', 'lambat', 'besar', 'kecil', 'panjang',
            'pendek', 'tinggi', 'rendah', 'berat', 'ringan', 'jelas', 'pasti',
            'aman', 'bebas', 'mudah', 'sulit', 'indah', 'bagus', 'jelek',
            'enak', 'manis', 'pahit', 'asam', 'asin', 'panas', 'dingin',
            'hangat', 'sejuk', 'teduh', 'gelap', 'terang', 'siang', 'malam',
            'pagi', 'sore', 'petang', 'pukul', 'waktu', 'tanggal', 'bulan',
            'tahun', 'abad', 'zaman', 'belum', 'sudah', 'telah', 'akan',
            'sedang', 'lagi', 'pernah', 'belum', 'kapan', 'dimana', 'bagaimana',
            'mengapa', 'apakah', 'siapa', 'berapa', 'semoga', 'semakin',
            'sekalian', 'seterusnya', 'selanjutnya', 'sebelumnya',
            'berikutnya', 'kebanyakan', 'setidaknya', 'paling', 'sekurang',
            'setinggi', 'sebesar', 'secepat', 'semurah', 'semahal',
            'seller', 'buyer', 'shipper', 'harga', 'katalog', 'katalogue',
            'merchandise', 'merchandisee', 'preorder', 'preorderr',
            'poster', 'posterr', 'sticker', 'stickerr', 'stikers', 'gantungan',
            'aksesoris', 'figurine', 'figura', 'cardboard', 'standee',
            'akrilik', 'acrylic', 'keychain', 'gantungan', 'miniature',
            'collectible', 'collectable', 'souvenir', 'merch', 'goodies',
            'freebies', 'bonus', 'hadiah', 'kado', 'bungkusan', 'box',
            'packaging', 'dus', 'plastik', 'amplop', 'invoice', 'resi',
            'tahap', 'tahapan', 'pembayaran', 'pengiriman', 'pemesanan',
            'pemesan', 'penjual', 'pembeli', 'admin', 'adm', 'fee',
            'ongkir', 'ongkos', 'ongkirim', 'ongkos kirim', 'pax',
            'slot', 'order', 'commision', 'catalog', 'catalogue',
            'photos', 'picture', 'picture', 'photo', 'foto', 'gambar',
            'condition', 'kondisi', 'used', 'second', 'bekas', 'baru',
            'segel', 'sealed', 'open', 'display', 'sample', 'contoh',
            'video', 'vidio', 'testimoni', 'review', 'rating', 'ulasan',
            'bintang', 'stars', 'trusted', 'legit', 'trust', 'garansi',
            'return', 'refund', 'exchange', 'tukar', 'ganti', 'rusak',
            'cacat', 'defect', 'minus', 'sobek', 'robek', 'lecek',
            'kotor', 'debu', 'jamur', 'berjamur', 'berdebu', 'berkarat',
            'karat', 'berkarat', 'fading', 'luntur', 'pudar', 'kupas',
            'terkelupas', 'lepas', 'putus', 'patah', 'retak', 'pecah',
            'kendur', 'longgar', 'kencang', 'ketat', 'melar', 'besar',
            'kempes', 'penyok', 'penyok', 'menguning', 'yellowing',
        }:
            continue
        found.add(word.title())

    # Clean up found names
    _user_kw_lower = {k.lower() for k in (user_keywords or [])}
    bad_tlds = {'.com', '.co', '.id', '.net', '.org', '.io', '.my'}
    cleaned = set()
    for name in found:
        nl = name.lower()
        if nl not in _user_kw_lower and (nl in NOISE_WORDS or nl in SERIES_KEYWORDS):
            continue
        # Check if any individual word in a multi-word name is noise
        name_parts = nl.split()
        if len(name_parts) > 1 and any(p in NOISE_WORDS for p in name_parts):
            if nl not in _user_kw_lower:
                continue
        if len(name) < 3 and nl not in ('oc',):
            continue
        if len(name) < 4 and nl not in ('oc', 'oc)',):
            continue
        if len(name) > 40:
            continue
        if any(t in nl for t in bad_tlds):
            continue
        if re.search(r'(comifuro|cf\d+|frontier|looking|please|katalog|merchandise|https?://)', nl):
            continue
        if re.match(r'^\d+', name):
            continue
        if re.match(r'^[A-Z]+$', name) and len(name) <= 2:
            continue
        if nl not in KNOWN_CHARACTERS and nl not in _user_kw_lower and nl.endswith(('nya', 'ku', 'mu', 'kah', 'lah', 'pun')):
            continue
        cleaned.add(name)

    return list(cleaned)
