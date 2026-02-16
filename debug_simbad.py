from astroquery.simbad import Simbad

# Настраиваем запрос так же, как в основном коде
Simbad.reset_votable_fields()
Simbad.add_votable_fields('flux(V)', 'flux(I)', 'plx', 'ids')

print("--- ЗАПРОС К SIMBAD ДЛЯ RT AUR ---")
table = Simbad.query_object("RT Aur")

# Выводим все названия колонок, которые вернула база
print("\nСПИСОК ВСЕХ КОЛОНОК:")
print(table.colnames)

# Выводим саму строку данных, чтобы увидеть значения
print("\nДАННЫЕ:")
print(table)