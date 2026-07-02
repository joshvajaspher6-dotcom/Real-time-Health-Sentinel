#!/usr/bin/env python3
"""
TestSentry Dataset Generator Monitor
=====================================
Real-time progress tracker with countdown timer
"""

import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

def get_dataset_info():
    """Get current dataset info"""
    try:
        with open("data/training_dataset.json") as f:
            dataset = json.load(f)
        return dataset
    except:
        return []

def get_category_counts(dataset):
    """Count examples per category"""
    counts = {}
    for item in dataset:
        cat = item.get("category", "UNKNOWN")
        counts[cat] = counts.get(cat, 0) + 1
    return counts

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}GB"

def get_file_creation_time():
    """Get when data file was created"""
    try:
        stat = os.stat("data/training_dataset.json")
        return stat.st_ctime
    except:
        return time.time()

def calculate_eta(current, target, start_time):
    """Calculate estimated time to completion"""
    elapsed = time.time() - start_time
    if current == 0 or elapsed == 0:
        return None
    
    rate = current / elapsed  # examples per second
    if rate == 0:
        return None
    
    remaining = target - current
    eta_seconds = remaining / rate
    return eta_seconds

def print_progress_bar(current, target, width=40):
    """Print a fancy progress bar"""
    percent = (current / target) * 100
    filled = int(width * current / target)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percent:.1f}%"

def monitor_generation():
    """Main monitoring loop"""
    TARGET = 3000
    file_start_time = get_file_creation_time()
    start_time = time.time()
    last_count = 0
    
    print("\n" + "="*80)
    print("🎯 TestSentry Dataset Generation Monitor")
    print("="*80 + "\n")
    print("Starting monitor (checking every 10 seconds)...\n")
    
    while True:
        try:
            dataset = get_dataset_info()
            current = len(dataset)
            
            # Use file creation time as reference
            elapsed = time.time() - file_start_time
            
            if current == last_count and current > 0:
                # No progress, still waiting for next batch
                print(f"\r⏳ Waiting for next batch... ({current}/3000 | {time.strftime('%H:%M:%S', time.gmtime(elapsed))} elapsed)", end="", flush=True)
                time.sleep(1)
                continue
            
            # Clear screen for update
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("="*80)
            print("🎯 TestSentry Dataset Generation Monitor")
            print("="*80 + "\n")
            
            eta_seconds = calculate_eta(current, TARGET, file_start_time)
            
            # Progress bar
            print(f"📊 Overall Progress:")
            print(f"   {print_progress_bar(current, TARGET)}")
            print(f"   {current}/3000 examples generated\n")
            
            # Statistics
            file_size = os.path.getsize("data/training_dataset.json")
            rate = current / elapsed if elapsed > 0 else 0
            
            print(f"📈 Statistics:")
            print(f"   Rate: {rate:.2f} examples/sec ({rate*60:.0f} examples/min)")
            print(f"   File Size: {format_size(file_size)}")
            print(f"   Elapsed: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}")
            
            # ETA with countdown
            if eta_seconds and eta_seconds > 0:
                eta_datetime = datetime.now() + timedelta(seconds=eta_seconds)
                remaining_formatted = time.strftime('%H:%M:%S', time.gmtime(eta_seconds))
                print(f"   ⏱️  ETA: {eta_datetime.strftime('%H:%M:%S')} ({remaining_formatted} remaining)")
            else:
                print(f"   ⏱️  ETA: Calculating...")
            
            # Category breakdown
            counts = get_category_counts(dataset)
            print(f"\n📋 Category Breakdown ({len(counts)} categories):\n")
            
            # Sort by count
            sorted_cats = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            
            # Pytest categories
            pytest_cats = [c for c in sorted_cats if 'PYTEST' in c[0]]
            if pytest_cats:
                total_pytest = sum(c[1] for c in pytest_cats)
                print(f"   🧪 pytest ({total_pytest} total):")
                for cat, count in pytest_cats:
                    pct = (count / 103) * 100
                    bar = "▓" * (count // 11) + "░" * ((103 - count) // 11)
                    print(f"      {cat:30s} {count:3d}/103 [{bar}] {pct:5.1f}%")
            
            # Playwright categories
            pw_cats = [c for c in sorted_cats if 'PLAYWRIGHT' in c[0]]
            if pw_cats:
                total_pw = sum(c[1] for c in pw_cats)
                print(f"\n   🎭 Playwright ({total_pw} total):")
                for cat, count in pw_cats:
                    pct = (count / 103) * 100
                    bar = "▓" * (count // 11) + "░" * ((103 - count) // 11)
                    print(f"      {cat:30s} {count:3d}/103 [{bar}] {pct:5.1f}%")
            
            # Selenium categories
            sel_cats = [c for c in sorted_cats if 'SELENIUM' in c[0]]
            if sel_cats:
                total_sel = sum(c[1] for c in sel_cats)
                print(f"\n   🤖 Selenium ({total_sel} total):")
                for cat, count in sel_cats:
                    pct = (count / 103) * 100
                    bar = "▓" * (count // 11) + "░" * ((103 - count) // 11)
                    print(f"      {cat:30s} {count:3d}/103 [{bar}] {pct:5.1f}%")
            
            # E2E & Services
            other_cats = [c for c in sorted_cats if c[0] not in [cat[0] for cat in pytest_cats + pw_cats + sel_cats]]
            if other_cats:
                total_other = sum(c[1] for c in other_cats)
                print(f"\n   🔗 E2E & Services ({total_other} total):")
                for cat, count in other_cats:
                    pct = (count / 103) * 100
                    bar = "▓" * (count // 11) + "░" * ((103 - count) // 11)
                    print(f"      {cat:30s} {count:3d}/103 [{bar}] {pct:5.1f}%")
            
            print("\n" + "="*80)
            print("⏹️  Press Ctrl+C to stop monitoring (doesn't stop generation)")
            print("="*80 + "\n")
            
            last_count = current
            
            # Check if done
            if current >= TARGET:
                print(f"\n✅ GENERATION COMPLETE!")
                print(f"   {current}/3000 examples created")
                print(f"   Total time: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}")
                break
            
            time.sleep(10)  # Update every 10 seconds
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped (generation continues in background)")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_generation()
