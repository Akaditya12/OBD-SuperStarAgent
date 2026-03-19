#!/bin/bash

API_KEY=sk_d9a6407c14a20dee2de7e19744fbf3bacd959d50a4a993f1

TEXT="Sorry. The number you have dialled is invalid. But do not hang up. We have an exciting offer for you. Stand a chance to win one thousand Kwacha and five hundred Kwacha weekly on the Swipe and Win Quiz. Press 1 to subscribe at two Kwacha per day. Terms and conditions apply."

declare -A voices=(

["daniel"]="onwK4e9ZLuTAKqWW03F9"
["george"]="JBFqnCBsd6RMkjVDRZzb"
["eric"]="cjVigY5qzO86Huf0OWal"
["liam"]="TX3LPaxmHKxFdv7VOQHJ"
["adam"]="pNInz6obpgDQGcFmaJgB"
["brian"]="nPczCjzI2devNBz1zQrb"
["callum"]="N2lVS1w4EtoT3dr4eOWO"
["charlie"]="IKne3meq5aSn9XLyUdCD"

)

mkdir -p male_voice_tests

for name in "${!voices[@]}"; do
  voice_id=${voices[$name]}

  echo "Generating sample for $name..."

  curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/$voice_id" \
    -H "xi-api-key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"text\": \"$TEXT\",
      \"model_id\": \"eleven_multilingual_v2\",
      \"voice_settings\": {
        \"stability\": 0.72,
        \"similarity_boost\": 0.88,
        \"style\": 0.25,
        \"use_speaker_boost\": true
      },
      \"output_format\": \"pcm_16000\"
    }" \
    --output "male_voice_tests/${name}.wav"

done

echo "All male IVR voice samples generated in ./male_voice_tests"
