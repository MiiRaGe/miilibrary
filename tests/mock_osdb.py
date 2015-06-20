def mock_get_movie_names(*args, **kwargs):
    return {}


def mock_get_movie_names2(*args, **kwargs):
    return {}


def mock_get_imdb_information(id):
    data = {
        '1981115': {'rating': '9.5', 'kind': 'movie', 'votes': '240548', 'language': ['English'],
                    'imdb_status': 'Cached',
                    'plot': 'When Jane Foster is possessed by a great power, Thor must protect her from a new threat of old times: the Dark Elves.',
                    'country': ['USA'], 'title': 'Thor: The Dark World',
                    'cover': 'http://ia.media-imdb.com/images/M/MV5BMTQyNzAwOTUxOF5BMl5BanBnXkFtZTcwMTE0OTc5OQ@@._V1_SY317_CR4,0,214,317_AL_.jpg',
                    'genres': [' Bullshit', 'London', ' Adventure', ' Romance'], 'from_redis': 'false',
                    'cast': {'_0000481': 'Alice Krige', '_0015382': 'Adewale Akinnuoye-Agbaje',
                             '_0038355': 'Tadanobu Asano', '_0001172': 'Christopher Eccleston',
                             '_1526352': 'Jaimie Alexander', '_1157048': 'Zachary Levi', '_1089991': 'Tom Hiddleston',
                             '_0000623': 'Rene Russo', '_0001745': u'Stellan Skarsg\xe5rd',
                             '_1165110': 'Chris Hemsworth', '_0000164': 'Anthony Hopkins',
                             '_0000204': 'Natalie Portman', '_0993507': 'Kat Dennings', '_0252961': 'Idris Elba',
                             '_0829032': 'Ray Stevenson'}, 'directors': {'_0851930': 'Alan Taylor'},
                    'request_from': 'cache_redis', 'year': '2013', 'duration': '112 min',
                    'goofs': 'In battles throughout the film, multiple stone columns are destroyed without any collapse of the building above. Perhaps in Asgardian architecture these columns are merely decorative, but their support is definitely required at Greenwich Palace.',
                    'aka': ['Argentina (Thor: Un mundo oscuro)',
                            u'Bulgaria (Bulgarian title) (\u0422\u041e\u0420: \u0421\u0432\u0435\u0442\u044a\u0442 \u043d\u0430 \u043c\u0440\u0430\u043a\u0430)',
                            'Brazil (Thor: O Mundo Sombrio)', 'Chile (Thor: Un mundo oscuro)',
                            'Germany (Thor - The Dark Kingdom)', 'Estonia (Thor: Pimeduse maailm)',
                            'Spain (Thor: El mundo oscuro)', u'France (Thor: Le monde des t\xe9n\xe8bres)',
                            'Georgia (Tori: bnei samkaro)', 'Greece (Thor 2: Skoteinos kosmos)',
                            'Croatia (Thor: Svijet tame)', u'Hungary (Thor: S\xf6t\xe9t vil\xe1g)',
                            "Israel (Hebrew title) (Thor: ha'olam ha'affel)",
                            'Italy (pre-release title) (Thor - Il mondo delle tenebre)', 'Italy (Thor: The Dark World)',
                            'Japan (English title) (Mighty Thor: Dark World)', 'Lithuania (Toras: Tamsos pasaulis)',
                            'Mexico (Thor: Un mundo oscuro)', 'Peru (Thor: Un mundo oscuro)',
                            'Poland (Thor: Mroczny swiat)', 'Portugal (Thor: O Mundo das Trevas)',
                            u'Romania (Thor: \xcentunericul)', u'Serbia (Tor: Mra\u010dni svet)',
                            u'Russia (\u0422\u043e\u0440 2: \u0426\u0430\u0440\u0441\u0442\u0432\u043e \u0442\u044c\u043c\u044b)',
                            u'Turkey (Turkish title) (Thor: Karanlik D\xfcnya)',
                            u'Ukraine (\u0422\u043e\u0440 2: \u0426\u0430\u0440\u0441\u0442\u0432\u043e \u0442\u0435\u043c\u0440\u044f\u0432\u0438)',
                            'USA (promotional title) (Marvel Thor: The Dark World)', 'USA (working title) (Thor 2)',
                            'USA (fake working title) (Thursday Mourning)',
                            'Vietnam (alternative title) (Thor 2: The Gioi Bong Toi)'],
                    'trivia': 'The stone creature Thor fights is a Kronan, an alien being that appeared in Thor\'s first comic, "Journey Into Mystery" #83. See more >>',
                    'id': '1981115'},
        '0800369': {'rating': '7.0', 'kind': 'movie', 'votes': '360424', 'language': ['English'],
                   'imdb_status': 'Cached',
                   'plot': 'The powerful but arrogant god Thor is cast out of Asgard to live amongst humans in Midgard (Earth), where he soon becomes one of their finest defenders.',
                   'country': ['USA'], 'title': 'Thor',
                   'cover': 'http://ia.media-imdb.com/images/M/MV5BMTYxMjA5NDMzNV5BMl5BanBnXkFtZTcwOTk2Mjk3NA@@._V1_SX214_AL_.jpg',
                   'genres': [' Action', ' Adventure', ' Fantasy'], 'from_redis': 'false',
                   'cast': {'_0038355': 'Tadanobu Asano', '_0163988': 'Clark Gregg', '_0000623': 'Rene Russo',
                            '_0056770': 'Adriana Barraza', '_1089991': 'Tom Hiddleston', '_2796047': 'Josh Dallas',
                            '_0001745': u'Stellan Skarsg\xe5rd', '_0272173': 'Colm Feore',
                            '_1526352': 'Jaimie Alexander', '_1165110': 'Chris Hemsworth',
                            '_0000164': 'Anthony Hopkins', '_0000204': 'Natalie Portman', '_0993507': 'Kat Dennings',
                            '_0252961': 'Idris Elba', '_0829032': 'Ray Stevenson'},
                   'directors': {'_0923736': 'Joss Whedon', '_0000110': 'Kenneth Branagh'}, 'year': '2011',
                   'request_from': 'cache_redis', 'tagline': 'Two worlds. One hero.', 'duration': '115 min',
                   'goofs': 'The hammer landed about 50 miles to the west of the town (according to the man in the diner). When Sif and Co. arrive, the SHIELD agent at the console says that it was about 50 miles to the north-west, placing it 75-80 miles from the town. Yet, when the Destroyer arrived, which was at the same location as Sif and Co, it was clearly on the outskirts of town.',
                   'aka': ['Argentina (Thor)',
                           u'Bulgaria (Bulgarian title) (\u0422\u041e\u0420: \u0411\u043e\u0433\u044a\u0442 \u043d\u0430 \u0433\u0440\u044a\u043c\u043e\u0442\u0435\u0432\u0438\u0446\u0438\u0442\u0435)',
                           'Colombia (Thor)', 'Denmark (Thor)', 'Greece (Thor)', 'Hungary (Thor)',
                           'Israel (alternative title) (Hebrew title) (Thor)', 'Japan (English title) (Mighty Thor)',
                           'Lithuania (Toras)', 'Mexico (Thor)', 'Peru (Thor)', 'Portugal (Thor)', 'Serbia (Tor)',
                           u'Russia (\u0422\u043e\u0440)', 'Sweden (Thor)', 'Turkey (Turkish title) (Thor)',
                           u'Ukraine (\u0422\u043e\u0440)', 'USA (fake working title) (Manhattan)',
                           'USA (original script title) (Thor, God of Thunder)', 'Uruguay (Thor)', 'Venezuela (Thor)',
                           'Venezuela (3-D version) (Thor 3D)', 'Vietnam (Than Sam Thor)',
                           'World-wide (English title) (copyright title) (The Mighty Thor)'],
                   'trivia': "Tom Hiddleston was chosen after previously collaborating with Kenneth Branagh on the theatrical play 'Ivanov' and the TV series Wallander (2008). See more >>",
                   'id': '0800369'},
    }
    return data[id.replace('t', '')]
