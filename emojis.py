def get_emoji(emoji_name):
    # Mapping of emoji names to their string representations
    emoji_mapping = {
        'heart_emoji': '<:heartlife:1150995915491000370>',
        'stamina_emoji': '<:endurance:1150995498342297610>',
        'strength_emoji': '<:strength:1150994770026569788>',
        'Health Potion': '<:health:1164232136753156098>',
        'Stamina Potion': '<:stamina:1164232132898607105>',
        'Super Stamina Potion': '<:super_stamina:1164232134672785541>',
        'Super Health Potion': '<:super_health:1164232129874509935>',
        'human_exemplar_emoji': '<:human_seafarer:1052760015372562453>',
        'dwarf_exemplar_emoji': '<:dwarf_glimmeringclan:1052760138987098122>',
        'orc_exemplar_emoji': '<:orcsofthelonghunt:1052760210357375046>',
        'halfling_exemplar_emoji': '<:halflinglongsong:1052760240954822678>',
        'elf_exemplar_emoji': '<:elf_darksun:1052760309875622009>',
        'Materium': '<:mtrm:1148449848085979167>',
        'rip_emoji': '<:rip:1150987930320523315>',
        'coal_emoji': '<:coal:1156402825652338799>',
        'iron_emoji': '<:iron_ore:1156402842341478453>',
        'carbon_emoji': '<:carbon:1156402823748132874>',
        'pine_emoji': '<:pine:1156402846531588218>',
        'yew_emoji': '<:Ico_yew:1157347841191198720>',
        'ash_emoji': '<:ash:1156402822083002389>',
        'poplar_emoji': '<:Ico_poplar:1157347835331743855>',
        'onyx_emoji': '<:onyx:1156402843767541901>',
        'deer_skin_emoji': '<:deer_skin:1156402830387720325>',
        'deer_part_emoji': '<:deer_part:1156402827296514108>',
        'rabbit_body_emoji': '<:Ico_rabbit_body:1157347837676363796>',
        'glowing_essence_emoji': '<:glowing_essence:1156402835257307197>',
        'wolf_skin_emoji': '<:ico_wolf_skin:1157347839064670358>',
        'goblin_crown_emoji': '<:GoblinCrown:1158371908488810618>',
        'coppers_emoji': '<:Mirandus_Coppers:1157348717008011345>',
        'common_emoji': '<:common:1157867391494144082>',
        'uncommon_emoji': '<:uncommon:1157867396078518394>',
        'rare_emoji': '<:rare:1157867394480492654>',
        'epic_emoji': '<:epic:1157867392416895037>',
        'legendary_emoji': '<:legendary:1157867393494810664>',
        'Woodcleaver': '<:Woodcleaver:1164763706593390602>',
        'Stonebreaker': '<:Stonebreaker:1164763700826214410>',
        'Ironhide': '<:Ironhide:1164763703879675954>',
        'Loothaven': '<:Loothaven:1164763702365519902>',
        'Mightstone': '<:Mightstone:1164763698326405141>',
        'Ash Strip': '<:AshStrip:1164773130728906763>',
        'Bread': '<:Bread:1164773141604737145>',
        'Brigandine Armor': '<:BrigandineArmor:1164773159749308416>',
        'Brigandine Boots': '<:BrigandineBoots:1164773176216137748>',
        'Brigandine Gloves': '<:BrigandineGloves:1164773185909170266>',
        'Buckler': '<:Buckler:1164773199091863614>',
        'Charcoal': '<:Charcoal:1164773210676547615>',
        'Club': '<:Club:1164773224433856512>',
        'Flax': '<:Flax:1164773240082804766>',
        'Flour': '<:Flour:1164773254460866560>',
        'Hammer': '<:Hammer:1164773266590793748>',
        'Iron': '<:Iron:1164773279056269322>',
        'Lantern of the Sun': '<:LanteroftheSun:1164773292192837683>',
        'Large Shield': '<:LargeShield:1164773305555894342>',
        'Leather Armor': '<:LeatherArmor:1164773316104564786>',
        'Leather Boots': '<:LeatherBoots:1164773325810176020>',
        'Leather Gloves': '<:LeatherGloves:1164773332814667857>',
        'Leather Straps': '<:LeatherStraps:1164773342436393021>',
        'Leather': '<:Leather:1164773354180448316>',
        'Linen Armor': '<:LinenArmor:1164773370471129138>',
        'Linen Boots': '<:LinenBoots:1164773387328032840>',
        'Linen Gloves': '<:LinenGloves:1164773398732357723>',
        'Linen Thread': '<:LinenThread:1164773412854566932>',
        'Linen': '<:Linen:1164773424049164358>',
        'Long Bow': '<:LongBow:1164773435734491156>',
        'Long Spear': '<:LongSpear:1164773450515218502>',
        'Long Sword': '<:LongSword:1164773460015325194>',
        'Champion Sword': '<:champion_sword:1157417006606327929>',
        'Padded Armor': '<:PaddedArmor:1164773474510843994>',
        'Padded Boots': '<:PaddedBoots:1164773505951354880>',
        'Padded Gloves': '<:PaddedGloves:1164773518555234315>',
        'Pine Strip': '<:PineStrip:1164773534443249694>',
        'Pole': '<:Pole:1164773552025763870>',
        'Poplar Strip': '<:PoplarStrip:1164773563107115089>',
        'Rabbit Meat': '<:RabbitMeat:1164773578634444862>',
        'Ring of Discord': '<:RingofDiscord:1164773589975842826>',
        'Short Bow': '<:ShortBow:1164773603628286003>',
        'Short Spear': '<:ShortSpear:1164773616731312168>',
        'Short Sword': '<:ShortSword:1164773628320153681>',
        'Sinew': '<:Sinew:1164773640999538718>',
        'Small Shield': '<:SmallShield:1164773656120021002>',
        'Steel': '<:Steel:1164773666744184923>',
        'Thick Pole': '<:ThickPole:1164773680442785882>',
        'Tough Leather Straps': '<:ToughLeatherStraps:1164773694552428567>',
        'Tough Leather': '<:ToughLeather:1164773707504427109>',
        'Trencher': '<:Trencher:1164773720729075783>',
        'Venison': '<:Venison:1164780154816581632>',
        'War Hammer': '<:WarHammer:1164780167256870912>',
        'Wheat': '<:Wheat:1164780177843306506>',
        'Yew Strip': '<:YewStrip:1164780188681392199>',
        'Carbon': '<:carbon:1156402823748132874>',
        'Voltaic Sword': '<:voltaic_sword:1157417008145629304>',
        'Champion Spear': '<:champion_spear:1157417004756648086>',
        'Champion Bow': '<:champion_bow:1157417003393486858>',
        'Ranarr': '<:Ranarr:1165469166870990868>',
        'Spirit Weed': '<:SpiritWeed:1165469173753839656>',
        'Snapdragon': '<:Snapdragon:1165469161837834341>',
        'Bloodweed': '<:Bloodweed:1165469363311235112>',
        'left_click': '<:LeftClick:1160445973559001219>',
        'right_click': '<:RightClick:1160445974771154984>',
        'q': '<:Q_:1160444478046359724>',
        'e': '<:E_:1160444475676565544>'
    }

    # Return the appropriate emoji string, or an empty string if not found
    return emoji_mapping.get(emoji_name, "")