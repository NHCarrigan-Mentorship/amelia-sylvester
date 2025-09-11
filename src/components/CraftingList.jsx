import { useState, useMemo } from 'react';
import craftingData from '../data/crafting_data.json';
import '../styles/crafting-list.css';

const RARITY_DISPLAY_NAMES = {
  1: 'Common',
  2: 'Uncommon',
  3: 'Rare',
  4: 'Epic',
  5: 'Legendary'
}

const ItemList = () => {
  // States for search input and selected filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTiers, setSelectedTiers] = useState(new Set(['Any']));
  const [selectedRarities, setSelectedRarities] = useState(new Set(['Any']));

  // Pulls all unique tiers and rarities from crafting data
  const allTiers = useMemo(() => {
    const tiers = new Set();
    Object.values(craftingData).forEach(item => {
      if (item.tier !== undefined) {
        tiers.add(item.tier);
      }
    });
    return ['Any', ...Array.from(tiers).sort((a, b) => a - b)];
  }, [craftingData]);

  const allRarities = useMemo(() => {
    const rarities = new Set();
    Object.values(craftingData).forEach(item => {
      if (item.rarity !== undefined) {
        rarities.add(item.rarity);
      }
    });
    return ['Any', ...Array.from(rarities).sort()];
  }, [craftingData]);

  // Toggles filter selection
  const toggleFilter = (filterSet, setFilterSet, filter) => {
    setFilterSet(prev => {
      const newSelection = new Set(prev);

      if (filter === 'Any') {
        return new Set(['Any']);
      }

      if (newSelection.has(filter)) {
        newSelection.delete(filter);
        if (newSelection.size === 0) return new Set(['Any']);
      } else {
        newSelection.add(filter);
        newSelection.delete('Any');
      }
      return newSelection;
    });
  };

  // Filter items
  const filteredItems = useMemo(() => {
    return Object.entries(craftingData).filter(([id, item]) => {
      const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTier = selectedTiers.has('Any') || selectedTiers.has(item.tier);
      const matchesRarity = selectedRarities.has('Any') || selectedRarities.has(item.rarity);
      return matchesSearch && matchesTier && matchesRarity;
    });
  }, [searchTerm, selectedTiers, selectedRarities, craftingData]);

  return (
    <div className='display-content'>
      {/* Filters */}
      <div className='filters-content'>
        <h2>Filters</h2>
        {/* Tiers */}
        <div className='tiers-filter'>
          <h3>Tier</h3>
          {allTiers.map(tier => (
            <div key={tier}>
              <label>
                <input
                  type='checkbox'
                  checked={selectedTiers.has(tier)}
                  onChange={() => toggleFilter(selectedTiers, setSelectedTiers, tier)}
                />
                {tier === 'Any' ? 'Any Tier' : `Tier ${tier}`}
              </label>
            </div>
          ))}
        </div>

        {/* Rarity */}
        <div>
          <h3>Rarity</h3>
          {allRarities.map(rarity => (
            <div key={rarity}>
              <label>
                <input
                  type='checkbox'
                  checked={selectedRarities.has(rarity)}
                  onChange={() => toggleFilter(selectedRarities, setSelectedRarities, rarity)}
                />
                {rarity === 'Any' ? 'Any Rarity' : RARITY_DISPLAY_NAMES[rarity] || `Unknown (${rarity})`}
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Search & Results */}
      <div>
        <div style={{ marginBottom: '20px' }}>
          <input
            type="text"
            placeholder='Search items by name...'
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ width: '100%', padding: '10px', fontSize: '16px', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>

        {/* Filters Applied Summary */}
        <div style={{ marginBottom: '15px', color: '#666' }}>
          {!selectedTiers.has('Any') && (
            <span>Tier: {Array.from(selectedTiers).map(t => t === 'Any' ? 'Any' : `T${t}`).join(', ')}</span>
          )}
          {!selectedRarities.has('Any') && (
            <span>Rarity: {Array.from(selectedRarities).map(r => r === 'Any' ? 'Any' : RARITY_DISPLAY_NAMES[r] || r).join(', ')}</span>
          )}
        </div>

        {/* Results List */}
        <div style={{ maxHeight: 'calc(100vh - 150px)', overflowY: 'auto' }}>
          {filteredItems.length === 0 ? (
            <p>No items found matching your criteria.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {filteredItems.map(([id, item]) => (
                <li key={id} style={{ padding: '15px', borderBottom: '1px solid #eee', marginBottom: '10px', backgroundColor: '#f9f9f9' }}>
                  <strong>{item.name}</strong>
                  <div>Tier: {item.tier} | Rarity: {RARITY_DISPLAY_NAMES[item.rarity] || `Unknown (${item.rarity})`} | Type: {item.tag}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

export default ItemList;