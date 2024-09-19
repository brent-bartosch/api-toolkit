"""
Chain store lists for filtering marketplace datasets
"""

BEAUTY_CHAINS = [
    # Major Beauty Chains
    'Sally Beauty', 'Sally Beauty Supply', 'Ulta', 'Ulta Beauty',
    'Sephora', 'CosmoProf', 'Beauty Brands', 'Harmon Face Values',
    "Ricky's NYC", 'Beauty 360', 'Bluemercury', 'Trade Secret',
    'Beauty First', 'Perfumania', 'The Body Shop', 'Lush Cosmetics',
    'Bath & Body Works', "Victoria's Secret", 'Yankee Candle',

    # Department Stores with Beauty Sections
    'CVS', 'CVS Pharmacy', 'Walgreens', 'Rite Aid', 'Duane Reade',
    'Target', 'Walmart', 'Macy\'s', 'Nordstrom', 'JCPenney',
    'Kohl\'s', 'Dillard\'s', 'Lord & Taylor', 'Bloomingdale\'s'
]

GUN_CHAINS = [
    "Sportsman's Warehouse", 'Bass Pro Shops', "Cabela's",
    "Dick's Sporting Goods", 'Field & Stream', 'Big 5 Sporting Goods',
    'Gander Mountain', 'Gander Outdoors', 'Scheels',
    'Academy Sports + Outdoors', "Dunham's Sports", 'Turner\'s Outdoorsman',
    'Fin Feather Fur Outfitters', 'Guns & Ammo', 'Range USA',
    'Shoot Point Blank', 'The Range 702', 'Gun World'
]

def get_exclusion_list(category: str) -> list:
    """
    Get chain exclusion list for a category.

    Args:
        category: 'beauty', 'gun', or 'all'

    Returns:
        List of chain names to exclude
    """
    if category.lower() == 'beauty':
        return BEAUTY_CHAINS
    elif category.lower() == 'gun':
        return GUN_CHAINS
    elif category.lower() == 'all':
        return BEAUTY_CHAINS + GUN_CHAINS
    else:
        return []