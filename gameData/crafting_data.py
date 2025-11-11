import copy
import json
import os.path
import shutil

# Data sourced from BitCraft ToolBox (https://github.com/BitCraftToolBox/BitCraft_GameData)
# This repo houses a copy of the data from BitCraft online
data_root = 'BitCraft_GameData/static'
crafting_recipes= json.load(open(f'{data_root}/crafting_recipe_desc.json'))
extraction_recipes = json.load(open(f'{data_root}/extraction_recipe_desc.json'))
items = json.load(open(f'{data_root}/item_desc.json'))
item_lists = json.load(open(f'{data_root}/item_list_desc.json'))
cargo = json.load(open(f'{data_root}/cargo_desc.json'))
enemies = json.load(open(f'{data_root}/enemy_desc.json'))

# Icons sourced from Brico (https://github.com/BitCraftToolBox/brico)
# This repo houses/utilizes item icons that are seen within the game
icon_root = 'brico/frontend/public/assets/GeneratedIcons'

# Cargo offset: Used as a shift value to add to cargo ids to allow for items and cargo to exist in a single list
cargo_offset = 0xffffffff
# Ignored tags: Tags within item_desc.json that aren't needed for crafting
ignored_tags = ['DEVELOPER ITEM', 'Crushed Ore', 'Precious', 'Cosmetic Clothes', 'Letter', 'Journal Page', 'Ancient Research']
# Skill ids: Id # that attaches a specific game skill to the crafting of the item
skill_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
# Recipes order overrides: Orders recipes that use carvings before recipes that use diagrams
recipes_order_overrides = {
  1210004: [1210037, 1210038],
  2210004: [2210037, 2210038],
  3210004: [3210037, 3210038],
  4210004: [4210037, 4210038],
  5210004: [5210037, 5210038],
  6210004: [6210037, 6210038]
}
# Recipes order overrides by tag: Key is paired with all item types that are used to craft key type
recipes_order_overrides_by_tag = {
  'Fertilizer': ['Berry', 'Flower', 'Lake Fish Filet', 'Oceanfish Filet', 'Raw Meat', 'Food Waste'],
  'Catalyst': ['Grain Seeds', 'Filament Seeds', 'Vegetable Seeds']
}
crafting_data = {}

def rarity_to_number(rarity_str):
  rarity_map = {
    'Common': 1,
    'Uncommon': 2,
    'Rare': 3,
    'Epic': 4,
    'Legendary': 5
  }
  return rarity_map.get(rarity_str, 1) # Default rarity of 1 if not founds

#################################

# Find recipes
def find_recipes(id, is_cargo = False):
  recipes = []
  expected_type = "Cargo" if is_cargo else "Item"
  
  for recipe in crafting_recipes:
    for result in recipe['crafted_item_stacks']:
      if result['item_id'] == id and result['item_type'] == expected_type:
        consumed_items = []
        consumes_itself = False
        
        for consumed_item in recipe['consumed_item_stacks']:
          if consumed_item['item_id'] == id:
            consumes_itself = True
            break
          
          consumed_id = consumed_item['item_id'] + (cargo_offset if consumed_item['item_type'] == "Cargo" else 0)
          consumed_items.append({ 'id': consumed_id, 'quantity': consumed_item['quantity'] })
          
        if consumes_itself:
          continue
        
        recipe_data = {
          'level_requirements': recipe['level_requirements'][0],
          'consumed_items': consumed_items,
          'output_quantity': result['quantity'],
          'possibilities': {}
        }
        recipes.append(recipe_data)
  return recipes

#################################

# Find extraction skill
def find_extraction_skill(id, is_cargo = False):
  expected_type = "Cargo" if is_cargo else "Item"
  
  for recipe in extraction_recipes:
    for result_group in recipe['extracted_item_stacks']:
      result = result_group['item_stack']
      if result['item_id'] == id and result['item_type'] == expected_type:
        return recipe['level_requirements'][0]['skill_id']
      
  for enemy in enemies:
    for result_group in enemy['extracted_item_stacks']:
      result = result_group['item_stack']
      if result['item_id'] == id and result['item_type'] == expected_type:
        return enemy['experience_per_damage_dealt'][0]['skill_id']
  return -1 # Not found
all_craftable_items = set()

#################################

# Get recipe priority
def get_recipe_priority(target_id, recipe):
  if target_id in recipes_order_overrides.keys():
    for item in recipe['consumed_items']:
      if item['id'] in recipes_order_overrides[target_id]:
        return recipes_order_overrides[target_id].index(item['id'])
      
  target_tag = crafting_data[target_id]['tag']
  if target_tag in recipes_order_overrides_by_tag:
    for item in recipe['consumed_items']:
      if item['id'] not in crafting_data:
        continue
      consumed_item_tag = crafting_data[item['id']]['tag']
      if consumed_item_tag in recipes_order_overrides_by_tag[target_tag]:
        return recipes_order_overrides_by_tag[target_tag].index(consumed_item_tag)
      
  priority_bonus = 0
  if 'Tool' in target_tag:
    for consumed_item in recipe['consumed_items']:
      if consumed_item['id'] not in crafting_data:
        continue
      if crafting_data[consumed_item['id']]['tag'] == 'Scrap':
        priority_bonus += 10000
        break
      
  if not recipe['consumed_items']:
    return 999999
      
  item = recipe['consumed_items'][0]
  item_id = item['id']
  
  if item_id not in crafting_data:
    # print(f'Warning: Consumed item ID {item_id} not found in crafting_data for target {target_id}') # WARNING #
    return 999999
  
  item_rarity = crafting_data[item_id]['rarity']
  item_quantity = item['quantity']
  try:
    return (item_quantity + (1000 if item_id > cargo_offset else 0)) \
      * item_rarity * 100 / recipe['output_quantity'] \
      + sum(map(int, str(item_id))) + priority_bonus
  except (TypeError, ZeroDivisionError) as e:
    # Log the error for later investigation
    print(f"WARNING: Could not calculate priority for target {target_id}, recipe {recipe.get('name', 'unknown')}. Using default priority. Error: {e}")
    # Return a high number (low priority) so the recipe is sorted to the end, but the script doesn't crash
    return 999999

#################################

# Collect items
print('Collecting items...')
for item in items:
  id = item['id']
    
  if id > cargo_offset:
    print(f'FATAL: item id {id} exceeds uint32 range')
    os.exit(1)
    
  ignore_item = False
  for tag in ignored_tags:
    if tag in item['tag']:
      ignore_item = True
      break
    
  if ignore_item:
    continue
  
  recipes = find_recipes(id)
  extraction_skill = find_extraction_skill(id)
  is_craftable = len(recipes) > 0
  is_extractable = extraction_skill != -1
  is_recipe_item = 'Recipe:' in item['name'] or 'Diagram' in item['name'] or 'Carvings' in item['name']
    
  if not (is_craftable or is_extractable or is_recipe_item):
    continue
  
  crafting_data[id] = {
    'name': item['name'],
    'tier': item['tier'],
    'rarity': rarity_to_number(item['rarity']),
    'icon': item['icon_asset_name'],
    'recipes': find_recipes(id),
    'extraction_skill': find_extraction_skill(id),
    'tag': item['tag']
  }

#################################

# Collect cargo
print('Collecting cargo...')
for item in cargo:
  id = item['id']
  if id > cargo_offset:
    print(f'FATAL: item id {id} exceeds uint32 range')
    os.exit(1)
    
  crafting_data[cargo_offset + id] = {
      'name': item['name'],
      'tier': item['tier'],
      'rarity': rarity_to_number(item['rarity']),
      'icon': item['icon_asset_name'],
      'recipes': find_recipes(id, True),
      'extraction_skill': find_extraction_skill(id, True),
      'tag': item['tag']
    }
  
#################################

# Compare OldGenerated and Generated directories to consolidate item icons
generated_icons_path = 'brico/frontend/public/assets/GeneratedIcons'
old_generated_icons_path = 'brico/frontend/public/assets/OldGeneratedIcons'

print('Comparing and consolidating icon directories...')

# Get all WEBP files in both directories
generated_icons = set()
for root, dirs, files in os.walk(generated_icons_path):
  for file in files:
    if file.endswith('.webp'):
      relative_path = os.path.relpath(os.path.join(root, file), generated_icons_path)
      generated_icons.add(relative_path)

old_generated_icons = set()
for root, dirs, files in os.walk(old_generated_icons_path):
  for file in files:
    if file.endswith('.webp'):
      relative_path = os.path.relpath(os.path.join(root, file), old_generated_icons_path)
      old_generated_icons.add(relative_path)

# Find icons in OldGenerated but not in Generated
missing_in_generated = old_generated_icons - generated_icons
print(f"Found {len(missing_in_generated)} icons in OldGeneratedIcons that are missing from GeneratedIcons")

# Copy missing icons from OldGenerated to Generated
copied_count = 0
for icon_path in missing_in_generated:
  source_path = os.path.join(old_generated_icons_path, icon_path)
  dest_path = os.path.join(generated_icons_path, icon_path)
  
  # Create destination directory if DNE
  os.makedirs(os.path.dirname(dest_path), exist_ok=True)
  
  # Copy file
  shutil.copy2(source_path, dest_path)
  copied_count += 1
  print(f"Copied: {icon_path}")

print(f"Copied {copied_count} icons from OldGeneratedIcons to GeneratedIcons")

#################################

# Update/fix icon pathing to use item icons
print('Normalizing icon paths for web...')
missing_icons = []

for item_id, item_data in crafting_data.items():
    icon = item_data['icon']
    original_icon = icon
    
    # Extract just the filename part (remove any directory prefixes)
    if 'GeneratedIcons/' in icon:
        icon = icon.split('GeneratedIcons/')[-1]
    if 'OldGeneratedIcons/' in icon:
        icon = icon.split('OldGeneratedIcons/')[-1]
    if 'Items/GeneratedIcons/' in icon:
        icon = icon.split('Items/GeneratedIcons/')[-1]
    if 'Cargo/GeneratedIcons/' in icon:
        icon = icon.split('Cargo/GeneratedIcons/')[-1]
    if 'Other/GeneratedIcons/' in icon:
        icon = icon.split('Other/GeneratedIcons/')[-1]
    
    # Remove any brackets and content inside them
    if '[' in icon:
        icon = icon.split('[')[0]
    
    # Remove file extension if present
    icon = os.path.splitext(icon)[0]
    
    # Now reconstruct the proper path with GeneratedIcons/ prefix
    # Check if the icon should be in a subdirectory
    final_icon_path = f"GeneratedIcons/{icon}"
    
    # Check if the file exists
    icon_full_path = os.path.join('brico/frontend/public/assets', f"{final_icon_path}.webp")
    
    if not os.path.exists(icon_full_path):
        missing_icons.append(final_icon_path)
        item_data['icon'] = 'Unknown'
    else:
        item_data['icon'] = final_icon_path

if missing_icons:
    print('Missing icons:')
    for icon in sorted(set(missing_icons))[:10]:  # Show first 10 only
        print(f'   {icon}')
    if len(missing_icons) > 10:
        print(f'   ... and {len(missing_icons) - 10} more')
else:
    print('All icons found.')

#################################

# Set recipe order
print('Reorganizing recipes...')
try:
  for item in items:
    if item['tag'] == 'Crushed Ore':
      continue
    
    id = item['id']
    list_id = item['item_list_id']

    # Skip if not a bundle item
    if list_id == 0 or item['tier'] < 0:
      continue
    
    # Remove bundle item from crafting data
    if id in crafting_data:
      del crafting_data[id]
    else:
      continue
    
    for item_list in item_lists:
      if item_list['id'] != list_id:
        continue
      
      possible_recipes = {}

      # Process all possibilities in list
      for possibility in item_list['possibilities']:
        chance = possibility['probability']

        for result in possibility['items']:
          target_id = result['item_id'] + (cargo_offset if result['item_type'] == "Cargo" else 0)
          if target_id not in crafting_data:
            continue
          
          if crafting_data[target_id]['extraction_skill'] < 0:
            is_target_cargo = (target_id > cargo_offset)
            crafting_data[target_id]['extraction_skill'] = find_extraction_skill(id, is_target_cargo)

          if target_id not in possible_recipes:
            possible_recipes[target_id] = {}

          quantity = result['quantity']

          if quantity not in possible_recipes[target_id]:
            possible_recipes[target_id][quantity] = 0.0

          possible_recipes[target_id][quantity] += chance

      recipes = find_recipes(id)
      for target_id, possibilities in possible_recipes.items():
        # Filter out recipes that consume the target item
        filtered_recipes = []
        for recipe in recipes:
          consumes_target = any(ci['id'] == target_id for ci in recipe['consumed_items'])
          if not consumes_target:
            filtered_recipes.append(copy.deepcopy(recipe))

        # Add possibilities to each recipe
        new_recipes = copy.deepcopy(filtered_recipes)
        for recipe in new_recipes:
          # recipe['possibilities'] = {k: possibilities[k] for k in sorted(possibilities)}
          recipe['possibilities'] = possibilities.copy()

        crafting_data[target_id]['recipes'].extend(new_recipes)
      break
except Exception as e:
  print(f"ERROR during reorganization: {e}")
  import traceback
  traceback.print_exc()
  print("Continuing without reorganization...")

#################################

# Sort recipes and misc cleanup
print('Cleanup and sort recipes...')
for key, value in crafting_data.items():
  recipes = value['recipes']
  dedup_recipes = {json.dumps(r, sort_keys=True) for r in recipes}
  recipes = [json.loads(r) for r in dedup_recipes]
  recipes.sort(key=lambda recipe: get_recipe_priority(key, recipe))
  value['recipes'] = recipes

#################################

# Copy icons into src/assets
print('Copying icons into public/assets...')
source_icons_dir = icon_root
dest_icons_dir = '../public/assets/GeneratedIcons'

##
print(f"Source directory: {source_icons_dir}")
print(f"Destination directory: {dest_icons_dir}")
##

##
if not os.path.exists(source_icons_dir):
  print(f'ERROR: Source directory DNE: {source_icons_dir}')
  print('Current working directory:', os.getcwd())
  print('Files in current directory:', os.listdir('.'))
  if os.path.exists('../brico'):
    print('Found brico in parent directory')
    source_icons_dir = f'../{icon_root}'
    print(f'Trying alternative path: {source_icons_dir}')
##

# Create dest directory if DNE
os.makedirs(dest_icons_dir, exist_ok=True)

##
if not os.path.exists(source_icons_dir):
  print(f'ERROR: Source directory still DNE: {source_icons_dir}')
else:
  print(f'Source directory found: {source_icons_dir}')

  # Copy all icons from source to dest
  copied_count = 0
  for root, dirs, files in os.walk(source_icons_dir):
    for file in files:
      if file.endswith('.webp'):
        source_path = os.path.join(root, file)

        # Calculate relative path to maintain directory structure
        relative_path = os.path.relpath(source_path, source_icons_dir)
        dest_path = os.path.join(dest_icons_dir, relative_path)

        # Create dest directory if DNE
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Copy file
        shutil.copy2(source_path, dest_path)
        copied_count += 1

  print(f'Copied {copied_count} icons to {dest_icons_dir}')

#################################

# Save crafting data
output_path = '../src/data/crafting_data.json'
print(f'Saving crafting data to {output_path}...')
json.dump(crafting_data, open(output_path, 'w'), indent=2)
print('Data saved!')
print('Script completed. Press Enter to exit...')
input()