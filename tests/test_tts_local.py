
import sys
import os
import asyncio
import logging

# Add root directory to path to import su6i_yar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_sherpa():
    print("\n🧪 Testing Local TTS (Sherpa-ONNX)...")
    print("---------------------------------------")
    
    try:
        from su6i_yar import init_sherpa_engine, text_to_speech_sherpa, SHERPA_ENGINE
        import su6i_yar
    except ImportError as e:
        print(f"❌ Import Failed: {e}")
        return False

    # Force Init
    print("🔄 Initializing Engine...")
    su6i_yar.init_sherpa_engine()
    
    if su6i_yar.SHERPA_ENGINE is None:
        print("❌ Engine Initialization Failed (SHERPA_ENGINE is None)")
        return False
    else:
        print("✅ Engine Initialized Successfully")

    # Generate Audio
    print("🗣️  Generating Audio ('سلام دنیا')...")
    audio = await su6i_yar.text_to_speech_sherpa("سلام دنیا این یک تست است")
    
    if audio and audio.getbuffer().nbytes > 0:
        print(f"✅ Audio Generated! Size: {audio.getbuffer().nbytes} bytes")
        # Save to file for manual check
        with open("tests/test_output.wav", "wb") as f:
            f.write(audio.getbuffer())
        print("💾 Saved to tests/test_output.wav")
        return True
    else:
        print("❌ Audio Generation Failed (Empty or None)")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sherpa())
    if success:
        print("\n🎉 TEST PASSED: Model 2 is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 TEST FAILED: Model 2 contains errors.")
        sys.exit(1)
