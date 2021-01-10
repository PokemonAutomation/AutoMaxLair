import requests

output_file = open("korean_translation.py", "w", encoding='utf8')
output_file.write("# DO NOT EDIT MANUALLY. This  file is automatically generated by create_korean_translation.py\n\n")

url = 'https://raw.githubusercontent.com/kwsch/PKHeX/master/PKHeX.Core/Resources/text/en/text_Species_en.txt'
r = requests.get(url, allow_redirects=True)
open('text_Species_en.txt', 'wb').write(r.content)

url = 'https://raw.githubusercontent.com/kwsch/PKHeX/master/PKHeX.Core/Resources/text/ko/text_Species_ko.txt'
r = requests.get(url, allow_redirects=True)
open('text_Species_ko.txt', 'wb').write(r.content)

species_english_file = open("text_Species_en.txt", "r", encoding='utf8')
species_korean_file = open("text_Species_ko.txt", "r", encoding='utf8')

species_english_lines = species_english_file.readlines()
species_korean_lines = species_korean_file.readlines()

output_file.write("translate_pokemon = {\n")
for i in range(0, len(species_english_lines)):
    output_file.write('\t"{english_string}" : "{korean_string}",\n'.format(english_string=species_english_lines[i].rstrip("\n"),korean_string=species_korean_lines[i].rstrip("\n")))
output_file.write("}\n\n")

species_english_file.close()
species_korean_file.close()



url = 'https://raw.githubusercontent.com/kwsch/PKHeX/master/PKHeX.Core/Resources/text/en/text_Abilities_en.txt'
r = requests.get(url, allow_redirects=True)
open('text_Abilities_en.txt', 'wb').write(r.content)

url = 'https://raw.githubusercontent.com/kwsch/PKHeX/master/PKHeX.Core/Resources/text/ko/text_Abilities_ko.txt'
r = requests.get(url, allow_redirects=True)
open('text_Abilities_ko.txt', 'wb').write(r.content)

abilities_english_file = open("text_Abilities_en.txt", "r", encoding='utf8')
abilities_korean_file = open("text_Abilities_ko.txt", "r", encoding='utf8')

abilities_english_lines = abilities_english_file.readlines()
abilities_korean_lines = abilities_korean_file.readlines()

output_file.write("translate_ability = {\n")
for i in range(0, len(abilities_english_lines)):
    output_file.write('\t"{english_string}" : "{korean_string}",\n'.format(english_string=abilities_english_lines[i].rstrip("\n"),korean_string=abilities_korean_lines[i].rstrip("\n")))
# todo hack
output_file.write('\t"Compoundeyes" : "복안"\n')
# todo hack
output_file.write("}\n\n")

species_english_file.close()
species_korean_file.close()



url = 'https://raw.githubusercontent.com/kwsch/PKHeX/master/PKHeX.Core/Resources/text/en/text_Types_en.txt'
r = requests.get(url, allow_redirects=True)
open('text_Types_en.txt', 'wb').write(r.content)

url = 'https://raw.githubusercontent.com/kwsch/PKHeX/master/PKHeX.Core/Resources/text/ko/text_Types_ko.txt'
r = requests.get(url, allow_redirects=True)
open('text_Types_ko.txt', 'wb').write(r.content)

types_english_file = open("text_Types_en.txt", "r", encoding='utf8')
types_korean_file = open("text_Types_ko.txt", "r", encoding='utf8')

types_english_lines = types_english_file.readlines()
types_korean_lines = types_korean_file.readlines()

output_file.write("translate_type = {\n")
for i in range(0, len(types_english_lines)):
    output_file.write('\t"{english_string}" : "{korean_string}",\n'.format(english_string=types_english_lines[i].rstrip("\n"),korean_string=types_korean_lines[i].rstrip("\n")))
output_file.write('\t"" : ""\n')
output_file.write("}\n\n")

types_english_file.close()
types_korean_file.close()