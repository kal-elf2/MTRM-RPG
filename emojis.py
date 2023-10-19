def get_emoji(emoji_name):
    # Mapping of emoji names to their string representations
    emoji_mapping = {
        'heart_emoji': '<:heartlife:1150995915491000370>',
        'stamina_emoji': '<:endurance:1150995498342297610>',
        'strength_emoji': '<:strength:1150994770026569788>',
        'potion_health': '<:health:1164232136753156098>',
        'potion_stamina': '<:stamina:1164232132898607105>',
        'potion_super_stamina': '<:super_stamina:1164232134672785541>',
        'potion_super_health': '<:super_health:1164232129874509935>',
        'human_exemplar_emoji': '<:human_seafarer:1052760015372562453>',
        'dwarf_exemplar_emoji': '<:dwarf_glimmeringclan:1052760138987098122>',
        'orc_exemplar_emoji': '<:orcsofthelonghunt:1052760210357375046>',
        'halfling_exemplar_emoji': '<:halflinglongsong:1052760240954822678>',
        'elf_exemplar_emoji': '<:elf_darksun:1052760309875622009>',
        'mtrm_emoji': '<:mtrm:1148449848085979167>',
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
        'deer_parts_emoji': '<:deer_part:1156402827296514108>',
        'rabbit_body_emoji': '<:Ico_rabbit_body:1157347837676363796>',
        'glowing_essence_emoji': '<:glowing_essence:1156402835257307197>',
        'wolf_skin_emoji': '<:ico_wolf_skin:1157347839064670358>',
        'coppers_emoji': '<:Mirandus_Coppers:1157348717008011345>',
        'common_emoji': '<:common:1157867391494144082>',
        'uncommon_emoji': '<:uncommon:1157867396078518394>',
        'rare_emoji': '<:rare:1157867394480492654>',
        'epic_emoji': '<:epic:1157867392416895037>',
        'legendary_emoji': '<:legendary:1157867393494810664>'
    }

    # Return the appropriate emoji string, or an empty string if not found
    return emoji_mapping.get(emoji_name, "")