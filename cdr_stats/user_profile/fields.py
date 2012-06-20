# encoding: utf-8

#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.utils.translation import ugettext as _
from django.db import models
from django.conf import settings


_using_south = 'south' in settings.INSTALLED_APPS
if _using_south:
    try:
        from south.modelsinspector import add_introspection_rules
    except ImportError:
        # Don't complain if South is not available
        _using_south = False


# Codes for the Representation of Names of Languages
# (Ref.: http://www.loc.gov/standards/iso639-2/php/code_list.php
#        via http://www.i18nguy.com/unicode/language-identifiers.html)
LANGUAGES = (
    ('aa', _('Afar')),
    ('ab', _('Abkhazian')),
    ('af', _('Afrikaans')),
    ('ak', _('Akan')),
    ('sq', _('Albanian')),
    ('am', _('Amharic')),
    ('ar', _('Arabic')),
    ('an', _('Aragonese')),
    ('hy', _('Armenian')),
    ('as', _('Assamese')),
    ('av', _('Avaric')),
    ('ae', _('Avestan')),
    ('ay', _('Aymara')),
    ('az', _('Azerbaijani')),
    ('ba', _('Bashkir')),
    ('bm', _('Bambara')),
    ('eu', _('Basque')),
    ('be', _('Belarusian')),
    ('bn', _('Bengali')),
    ('bh', _('Bihari languages')),
    ('bi', _('Bislama')),
    ('bo', _('Tibetan')),
    ('bs', _('Bosnian')),
    ('br', _('Breton')),
    ('bg', _('Bulgarian')),
    ('my', _('Burmese')),
    ('ca', _('Catalan; Valencian')),
    ('cs', _('Czech')),
    ('ch', _('Chamorro')),
    ('ce', _('Chechen')),
    ('zh', _('Chinese')),
    ('cu', _('Church Slavic; Old Slavonic; '
             'Church Slavonic; Old Bulgarian; Old Church Slavonic')),
    ('cv', _('Chuvash')),
    ('kw', _('Cornish')),
    ('co', _('Corsican')),
    ('cr', _('Cree')),
    ('cy', _('Welsh')),
    ('cs', _('Czech')),
    ('da', _('Danish')),
    ('de', _('German')),
    ('dv', _('Divehi; Dhivehi; Maldivian')),
    ('nl', _('Dutch; Flemish')),
    ('dz', _('Dzongkha')),
    ('el', _('Greek, Modern (1453-)')),
    ('en', _('English')),
    ('eo', _('Esperanto')),
    ('et', _('Estonian')),
    ('eu', _('Basque')),
    ('ee', _('Ewe')),
    ('fo', _('Faroese')),
    ('fa', _('Persian')),
    ('fj', _('Fijian')),
    ('fi', _('Finnish')),
    ('fr', _('French')),
    ('fr', _('French')),
    ('fy', _('Western Frisian')),
    ('ff', _('Fulah')),
    ('ka', _('Georgian')),
    ('de', _('German')),
    ('gd', _('Gaelic; Scottish Gaelic')),
    ('ga', _('Irish')),
    ('gl', _('Galician')),
    ('gv', _('Manx')),
    ('el', _('Greek, Modern (1453-)')),
    ('gn', _('Guarani')),
    ('gu', _('Gujarati')),
    ('ht', _('Haitian; Haitian Creole')),
    ('ha', _('Hausa')),
    ('he', _('Hebrew')),
    ('hz', _('Herero')),
    ('hi', _('Hindi')),
    ('ho', _('Hiri Motu')),
    ('hr', _('Croatian')),
    ('hu', _('Hungarian')),
    ('hy', _('Armenian')),
    ('ig', _('Igbo')),
    ('is', _('Icelandic')),
    ('io', _('Ido')),
    ('ii', _('Sichuan Yi; Nuosu')),
    ('iu', _('Inuktitut')),
    ('ie', _('Interlingue; Occidental')),
    ('ia', _('Interlingua (International Auxiliary Language Association)')),
    ('id', _('Indonesian')),
    ('ik', _('Inupiaq')),
    ('is', _('Icelandic')),
    ('it', _('Italian')),
    ('jv', _('Javanese')),
    ('ja', _('Japanese')),
    ('kl', _('Kalaallisut; Greenlandic')),
    ('kn', _('Kannada')),
    ('ks', _('Kashmiri')),
    ('ka', _('Georgian')),
    ('kr', _('Kanuri')),
    ('kk', _('Kazakh')),
    ('km', _('Central Khmer')),
    ('ki', _('Kikuyu; Gikuyu')),
    ('rw', _('Kinyarwanda')),
    ('ky', _('Kirghiz; Kyrgyz')),
    ('kv', _('Komi')),
    ('kg', _('Kongo')),
    ('ko', _('Korean')),
    ('kj', _('Kuanyama; Kwanyama')),
    ('ku', _('Kurdish')),
    ('lo', _('Lao')),
    ('la', _('Latin')),
    ('lv', _('Latvian')),
    ('li', _('Limburgan; Limburger; Limburgish')),
    ('ln', _('Lingala')),
    ('lt', _('Lithuanian')),
    ('lb', _('Luxembourgish; Letzeburgesch')),
    ('lu', _('Luba-Katanga')),
    ('lg', _('Ganda')),
    ('mk', _('Macedonian')),
    ('mh', _('Marshallese')),
    ('ml', _('Malayalam')),
    ('mi', _('Maori')),
    ('mr', _('Marathi')),
    ('ms', _('Malay')),
    ('mk', _('Macedonian')),
    ('mg', _('Malagasy')),
    ('mt', _('Maltese')),
    ('mn', _('Mongolian')),
    ('mi', _('Maori')),
    ('ms', _('Malay')),
    ('my', _('Burmese')),
    ('na', _('Nauru')),
    ('nv', _('Navajo; Navaho')),
    ('nr', _('Ndebele, South; South Ndebele')),
    ('nd', _('Ndebele, North; North Ndebele')),
    ('ng', _('Ndonga')),
    ('ne', _('Nepali')),
    ('nl', _('Dutch; Flemish')),
    ('nn', _('Norwegian Nynorsk; Nynorsk, Norwegian')),
    ('nb', _('Bokmal, Norwegian; Norwegian Bokmal')),
    ('no', _('Norwegian')),
    ('ny', _('Chichewa; Chewa; Nyanja')),
    ('oc', _('Occitan (post 1500)')),
    ('oj', _('Ojibwa')),
    ('or', _('Oriya')),
    ('om', _('Oromo')),
    ('os', _('Ossetian; Ossetic')),
    ('pa', _('Panjabi; Punjabi')),
    ('fa', _('Persian')),
    ('pi', _('Pali')),
    ('pl', _('Polish')),
    ('pt', _('Portuguese')),
    ('ps', _('Pushto; Pashto')),
    ('qu', _('Quechua')),
    ('rm', _('Romansh')),
    ('ro', _('Romanian; Moldavian; Moldovan')),
    ('ro', _('Romanian; Moldavian; Moldovan')),
    ('rn', _('Rundi')),
    ('ru', _('Russian')),
    ('sg', _('Sango')),
    ('sa', _('Sanskrit')),
    ('si', _('Sinhala; Sinhalese')),
    ('sk', _('Slovak')),
    ('sk', _('Slovak')),
    ('sl', _('Slovenian')),
    ('se', _('Northern Sami')),
    ('sm', _('Samoan')),
    ('sn', _('Shona')),
    ('sd', _('Sindhi')),
    ('so', _('Somali')),
    ('st', _('Sotho, Southern')),
    ('es', _('Spanish; Castilian')),
    ('sq', _('Albanian')),
    ('sc', _('Sardinian')),
    ('sr', _('Serbian')),
    ('ss', _('Swati')),
    ('su', _('Sundanese')),
    ('sw', _('Swahili')),
    ('sv', _('Swedish')),
    ('ty', _('Tahitian')),
    ('ta', _('Tamil')),
    ('tt', _('Tatar')),
    ('te', _('Telugu')),
    ('tg', _('Tajik')),
    ('tl', _('Tagalog')),
    ('th', _('Thai')),
    ('bo', _('Tibetan')),
    ('ti', _('Tigrinya')),
    ('to', _('Tonga (Tonga Islands)')),
    ('tn', _('Tswana')),
    ('ts', _('Tsonga')),
    ('tk', _('Turkmen')),
    ('tr', _('Turkish')),
    ('tw', _('Twi')),
    ('ug', _('Uighur; Uyghur')),
    ('uk', _('Ukrainian')),
    ('ur', _('Urdu')),
    ('uz', _('Uzbek')),
    ('ve', _('Venda')),
    ('vi', _('Vietnamese')),
    ('vo', _('Volapuk')),
    ('cy', _('Welsh')),
    ('wa', _('Walloon')),
    ('wo', _('Wolof')),
    ('xh', _('Xhosa')),
    ('yi', _('Yiddish')),
    ('yo', _('Yoruba')),
    ('za', _('Zhuang; Chuang')),
    ('zh', _('Chinese')),
    ('zu', _('Zulu')),
)


class LanguageField(models.CharField):
    """Stores language codes as defined by ISO 639-1"""

    description = _("Stores language codes")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 2)
        kwargs.setdefault('choices', LANGUAGES)

        super(LanguageField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'CharField'

if _using_south:
    add_introspection_rules([], ['^djangomissing\.fields\.LanguageField'])
