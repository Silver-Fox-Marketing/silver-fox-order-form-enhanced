#!/usr/bin/env python3
"""
Quick Scraper Priority Assessment
Identify the most promising scrapers to optimize next based on website accessibility
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def test_website_accessibility(dealership_info):
    """Quick test of website accessibility"""
    name, url = dealership_info
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response_time = time.time() - start_time
        
        return {
            'name': name,
            'url': url,
            'accessible': response.status_code == 200,
            'status_code': response.status_code,
            'response_time': response_time,
            'content_length': len(response.content) if response.status_code == 200 else 0,
            'has_cloudflare': 'cloudflare' in response.text.lower(),
            'has_vehicles': 'vehicle' in response.text.lower() or 'inventory' in response.text.lower()
        }
    except Exception as e:
        return {
            'name': name,
            'url': url,
            'accessible': False,
            'error': str(e)[:100]
        }

def assess_priority_scrapers():
    """Assess priority scrapers for optimization"""
    print("🎯 QUICK SCRAPER PRIORITY ASSESSMENT")
    print("Testing website accessibility to prioritize optimization efforts")
    print("=" * 70)
    
    # Priority dealerships based on our previous analysis
    priority_dealerships = [
        ("Joe Machens Nissan", "https://www.joemachensnissan.com"),
        ("Joe Machens Hyundai", "https://www.joemachenshyundai.com"),
        ("BMW of West St Louis", "https://www.bmwofweststlouis.com"),
        ("Columbia Honda", "https://www.columbiahonda.com"),
        ("Frank Leta Honda", "https://www.frankletahonda.com"),
        ("Porsche St Louis", "https://www.porschestlouis.com"),
        ("Audi Rancho Mirage", "https://www.audiranchomirage.com"),
        ("Mini of St Louis", "https://www.miniofstlouis.com"),
        ("Spirit Lexus", "https://www.spiritlexus.com"),
        ("Suntrup Ford Kirkwood", "https://www.suntrupfordkirkwood.com"),
        ("Weber Chevrolet", "https://www.weberchev.com"),
        ("Thoroughbred Ford", "https://www.thoroughbredford.com"),
        ("Dave Sinclair Lincoln South", "https://www.davesinclairlincolnsouth.com"),
        ("Pappas Toyota", "https://www.pappastoyota.com"),
        ("Twin City Toyota", "https://www.twincitytoyota.com")
    ]
    
    print(f"Testing {len(priority_dealerships)} priority dealership websites...")
    print()
    
    # Test websites concurrently for speed
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_dealership = {
            executor.submit(test_website_accessibility, dealership): dealership 
            for dealership in priority_dealerships
        }
        
        for i, future in enumerate(as_completed(future_to_dealership), 1):
            try:
                result = future.result()
                results.append(result)
                
                name = result['name']
                if result['accessible']:
                    response_time = result['response_time']
                    cloudflare = "🛡️ CF" if result.get('has_cloudflare') else ""
                    vehicles = "🚗" if result.get('has_vehicles') else ""
                    print(f"[{i:2d}/15] ✅ {name:<25} ({response_time:.1f}s) {cloudflare} {vehicles}")
                else:
                    error = result.get('error', f"HTTP {result.get('status_code', 'Unknown')}")
                    print(f"[{i:2d}/15] ❌ {name:<25} ({error[:30]})")
                    
            except Exception as e:
                print(f"[{i:2d}/15] ❌ Error: {str(e)[:50]}")
    
    # Analyze results
    print("\n" + "=" * 70)
    print("📊 ASSESSMENT RESULTS")
    print("=" * 70)
    
    accessible = [r for r in results if r.get('accessible', False)]
    blocked = [r for r in results if not r.get('accessible', False)]
    
    print(f"✅ Accessible websites: {len(accessible)}")
    print(f"❌ Blocked/Error websites: {len(blocked)}")
    
    # Prioritize accessible sites by response time and features
    if accessible:
        # Sort by response time (faster = better for scraping)
        accessible_sorted = sorted(accessible, key=lambda x: x['response_time'])
        
        print(f"\n🎯 TOP PRIORITY FOR OPTIMIZATION (Fast & Accessible):")
        for i, site in enumerate(accessible_sorted[:8], 1):
            name = site['name']
            response_time = site['response_time']
            features = []
            if site.get('has_vehicles'):
                features.append("📋 Inventory")
            if site.get('has_cloudflare'):
                features.append("🛡️ Cloudflare")
            if site['response_time'] < 2.0:
                features.append("⚡ Fast")
            
            features_str = " ".join(features) if features else "Basic"
            print(f"   {i}. {name:<25} ({response_time:.1f}s) {features_str}")
    
    if blocked:
        print(f"\n⚠️ BLOCKED/PROBLEMATIC SITES:")
        for site in blocked:
            name = site['name']
            error = site.get('error', f"HTTP {site.get('status_code', 'Unknown')}")
            print(f"   ❌ {name:<25} {error[:40]}")
    
    # Recommendations
    print(f"\n🔧 OPTIMIZATION RECOMMENDATIONS:")
    
    if accessible:
        fastest_site = accessible_sorted[0]
        print(f"   🎯 START WITH: {fastest_site['name']}")
        print(f"      ⚡ Fastest response time: {fastest_site['response_time']:.1f}s")
        print(f"      📋 Has inventory content: {fastest_site.get('has_vehicles', False)}")
        print(f"      🛡️ Cloudflare protection: {fastest_site.get('has_cloudflare', False)}")
        
        print(f"\n   📋 NEXT 3 TARGETS:")
        for site in accessible_sorted[1:4]:
            cf_warning = " (⚠️ Cloudflare)" if site.get('has_cloudflare') else ""
            print(f"      • {site['name']}{cf_warning}")
    
    print(f"\n   ⚠️ AVOID FOR NOW:")
    print(f"      • Sites with Cloudflare protection")
    print(f"      • Sites with >3s response times") 
    print(f"      • Sites returning errors")
    
    print(f"\n✅ STRATEGY:")
    print(f"   1. Apply on-lot methodology to fastest accessible sites first")
    print(f"   2. Build momentum with successful optimizations")
    print(f"   3. Tackle problematic sites after proving methodology")
    
    return accessible_sorted

if __name__ == "__main__":
    start_time = time.time()
    
    prioritized_sites = assess_priority_scrapers()
    
    end_time = time.time()
    print(f"\n⏱️ Assessment completed in {end_time - start_time:.1f} seconds")
    
    if prioritized_sites:
        print(f"\n🎯 NEXT TARGET: {prioritized_sites[0]['name']}")
        print(f"Ready to apply on-lot filtering methodology!")