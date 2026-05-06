"""Test import of new scrcpy plugin"""
import sys

def test_import():
    """Test that the new scrcpy plugin can be imported"""
    print("Testing import of new scrcpy plugin...")
    
    try:
        # Try to import the plugin
        from async_adbc.plugins.scrcpy import ScrcpyPlugin
        print("✅ ScrcpyPlugin imported successfully")
        
        # Check if pyscrcpy is available
        from async_adbc.plugins.scrcpy import HAS_PYSCRCPY
        print(f"   HAS_PYSCRCPY: {HAS_PYSCRCPY}")
        
        if HAS_PYSCRCPY:
            print("✅ pyscrcpy is available")
        else:
            print("⚠️  pyscrcpy is not available (will raise RuntimeError on use)")
            
        # Check the class
        print(f"   Class name: {ScrcpyPlugin.__name__}")
        print(f"   Module: {ScrcpyPlugin.__module__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)