import { useMemo, useState } from 'react';
import craftingData from '../data/crafting_data.json';
import '../styles/crafting-list.css';
//import FilterDropdown from './FilterDropdown';
//import CraftingTree from './CraftingTree';

const RARITY_DISPLAY_COLORS = {
  1: 'var(--common-item-color)',
  2: 'var(--uncommon-item-color)',
  3: 'var(--rare-item-color)',
  4: 'var(--epic-item-color)',
  5: 'var(--legendary-item-color)'
}

const SKILL_DISPLAY_NAMES = {
  1: 'Any Skill',
  2: 'Forestry',
  3: 'Carpentry',
  4: 'Masonry',
  5: 'Mining',
  6: 'Smithing',
  7: 'Scholar',
  8: 'Leatherworking',
  9: 'Hunting',
  10: 'Tailoring',
  11: 'Farming',
  12: 'Fishing',
  13: 'Cooking',
  14: 'Foraging'
}

const TIER_OPTIONS = [
  { value: '', label: 'All Tiers' },
  { value: '1', label: 'Tier 1'},
  { value: '2', label: 'Tier 2'},
  { value: '3', label: 'Tier 3'},
  { value: '4', label: 'Tier 4'},
  { value: '5', label: 'Tier 5'},
  { value: '6', label: 'Tier 6'},
  { value: '7', label: 'Tier 7'},
  { value: '8', label: 'Tier 8'},
  { value: '9', label: 'Tier 9'},
  { value: '10', label: 'Tier 10'}
];

const ItemList = () => {
  // States for search input and selected filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTier, setSelectedTier] = useState('');
  const [selectedSkill, setSelectedSkill] = useState('1');
  const [selectedItem, setSelectedItem] = useState(null);
  const [craftingQuantity, setCraftingQuantity] = useState(1);

  // Filter items
  const filteredItems = useMemo(() => {
    return Object.entries(craftingData).filter(([id, item]) => {
      const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTier = selectedTier === '' || item.tier.toString() === selectedTier;
      const matchesSkill = selectedSkill === '1' || 
        item.recipes?.some(recipe => 
          recipe.level_requirements?.skill_id?.toString() === selectedSkill
        );
      return matchesSearch && matchesTier && matchesSkill;
    });
  }, [searchTerm, selectedTier, selectedSkill, craftingData]);

  return (
    <div className='display-content'>
      <div className='filters-content'>
          <h2>Filters</h2>
      </div>

      {/* Search & Filters */}
      <div>
        <div style={{ marginBottom: '20px' }} className="search-and-filters">
          <input
            type="text"
            id="search-bar"
            placeholder='Search item...'
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {/* Skill filter */}
          {/* <FilterDropdown
            options={Object.entries(SKILL_DISPLAY_NAMES).map(([value, label]) => ({
              value,
              label
            }))}
            value={selectedSkill}
            onChange={setSelectedSkill}
            placeholder="Any Skill"
          /> */}

          {/* Tier filter */}
          {/* <FilterDropdown
            options={TIER_OPTIONS}
            value={selectedTier}
            onChange={setSelectedTier}
            placeholder="Any Tier"
          /> */}
        </div>

        {/* Results */}
        <div className="items-grid">
          {filteredItems.length === 0 ? (
            <p>No items found matching your criteria.</p>
          ) : (
            filteredItems.map(([id, item]) => (
              <div
                key={id}
                className={`item-card ${selectedItem?.id === id ? 'selected' : ''}`}
                onClick={() => setSelectedItem({ id, ...item })}
                style={{ borderColor: `${RARITY_DISPLAY_COLORS[item.rarity]}`}}
              >
                <img
                  src={`/assets/${item.icon}.webp`}
                  alt={item.name}
                  className='item-icon'
                  // onError={(e) => {
                  //   e.target.src = '/assets/Unknown.webp';
                  // }}
                />
                <div className='item-name'>{item.name}</div>
              </div>
            ))
          )}
        </div>

        {/* {selectedItem && (
          <div className='selected-item-details'>
            <h3>{selectedItem.name}</h3>
            <p>Tier: {selectedItem.tier}, Rarity: {selectedItem.rarity}</p>
            <CraftingTree
              item={selectedItem}
              quantity={craftingQuantity}
              onQuantityChange={setCraftingQuantity}
            />
          </div>
        )} */}
      </div>
    </div>
  )
}

export default ItemList;