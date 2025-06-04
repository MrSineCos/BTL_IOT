# AI Chatbot for CoreIOT Platform

## Overview

This project is an AI-powered chatbot that interfaces with CoreIOT, an IoT platform built on ThingsBoard cloud server. The chatbot enables natural language interaction with IoT devices through WebSocket API communication, allowing users to query sensor data and control devices using conversational commands.

## Features

### 🤖 Natural Language Understanding (NLU)
- Processes user queries in natural language
- Extracts device and action intents from user input
- Supports multiple query types for different sensors

### 📊 Sensor Data Queries
- **Temperature**: Query DHT sensor for current temperature readings
- **Humidity**: Get humidity levels from DHT sensor
- **Gas Detection**: Monitor gas concentration from MQ sensor
- **Dust Levels**: Check dust concentration from GP sensor
- **Air Quality**: Comprehensive air quality report including all environmental parameters

### 🎛️ Device Control
- **Light Control**: Turn lights on/off and check status
- **Fan Control**: Control fan operation
- **Energy Monitoring**: Track energy consumption

### 🧠 AI Integration
- Powered by Google Gemma-3-12b model via OpenRouter API
- Intelligent intent parsing with JSON schema validation
- Fallback to guide-based responses for general questions

## Architecture

### Core Components

1. **function_exAI.py**: Main AI processing module
   - Intent parsing and NLU functionality
   - Device control logic
   - AI model integration

2. **mqttservice_coreiot.py**: IoT communication layer
   - MQTT client for ThingsBoard communication
   - WebSocket API integration
   - Telemetry data retrieval
   - Device attribute management

### Supported Devices
- **DHT**: Temperature and humidity sensor
- **MQ**: Gas detection sensor
- **GP**: Dust/particulate matter sensor
- **Air**: Comprehensive air quality monitoring
- **Light**: Smart lighting control
- **Fan**: Ventilation control

### Supported Actions
- `query_temperature`: Get current temperature
- `query_humidity`: Get humidity levels
- `query_gas`: Check gas concentration
- `query_dust`: Monitor dust levels
- `query_air`: Comprehensive air quality report
- `general_question`: Handle system information queries

## Technology Stack

- **Backend**: Python
- **IoT Platform**: ThingsBoard Cloud Server
- **Communication**: MQTT Protocol, WebSocket API
- **AI Model**: Google Gemma-3-12b (via OpenRouter)
- **NLU**: Custom intent parsing with JSON schema
- **Data Format**: JSON for structured responses

## API Integration Details

### HTTP APIs Used

#### 1. OpenRouter API (function_exAI.py)

**Base URL**: `https://openrouter.ai/api/v1`

##### Chat Completions API
- **Endpoint**: `POST /chat/completions`
- **Purpose**: Natural Language Understanding and Intent Parsing
- **Authentication**: Bearer Token
- **Content-Type**: `application/json`

**Request Structure**:
```json
{
  "model": "google/gemma-3-12b-it:free",
  "messages": [
    {
      "role": "system",
      "content": "You are an NLU module..."
    },
    {
      "role": "user",
      "content": "What's the temperature?"
    }
  ],
  "temperature": 0.1,
  "max_tokens": 500,
  "stream": false
}
```

**Response Structure**:
```json
{
  "choices": [
    {
      "message": {
        "content": "{\"device\": \"DHT\", \"action\": \"query_temperature\"}"
      }
    }
  ]
}
```

#### 2. ThingsBoard REST API (mqttservice_coreiot.py)

**Base URL**: `https://{THINGSBOARD_HOST}/api`

##### Telemetry API
- **Endpoint**: `GET /plugins/telemetry/DEVICE/{deviceId}/values/timeseries`
- **Purpose**: Retrieve latest sensor telemetry data
- **Authentication**: JWT Token via `X-Authorization` header
- **Parameters**: 
  - `keys`: Comma-separated list of telemetry keys (temperature, humidity, mq2, dust)

**Request Example**:
```http
GET /api/plugins/telemetry/DEVICE/abc123/values/timeseries?keys=temperature,humidity
X-Authorization: Bearer eyJhbGciOiJIUzUxMiJ9...
```

**Response Structure**:
```json
{
  "temperature": [
    {
      "ts": 1640995200000,
      "value": "25.3"
    }
  ],
  "humidity": [
    {
      "ts": 1640995200000,
      "value": "65.2"
    }
  ]
}
```

### WebSocket APIs Used

#### 1. ThingsBoard WebSocket API (mqttservice_coreiot.py)

**Base URL**: `wss://{THINGSBOARD_HOST}/api/ws`

##### Real-time Telemetry Subscription
- **Protocol**: WebSocket over MQTT
- **Purpose**: Real-time sensor data streaming
- **Authentication**: JWT Token in connection parameters

**Connection Setup**:
```javascript
// WebSocket connection with JWT authentication
wss://thingsboard.cloud/api/ws?token=eyJhbGciOiJIUzUxMiJ9...
```

**Subscription Message**:
```json
{
  "cmdId": 1,
  "entityType": "DEVICE",
  "entityId": "device-uuid",
  "scope": "LATEST_TELEMETRY",
  "type": "TIMESERIES"
}
```

**Real-time Data Response**:
```json
{
  "subscriptionId": 1,
  "data": {
    "temperature": [
      {
        "ts": 1640995200000,
        "value": "25.3"
      }
    ]
  }
}
```

### MQTT APIs Used

#### 1. ThingsBoard MQTT API (mqttservice_coreiot.py)

**Broker**: `{THINGSBOARD_HOST}:1883`

##### Telemetry Publishing
- **Topic**: `v1/devices/me/telemetry`
- **Purpose**: Send sensor data to ThingsBoard
- **Authentication**: Device Access Token
- **QoS**: 1

**Payload Example**:
```json
{
  "temperature": 25.3,
  "humidity": 65.2,
  "mq2": 15.7,
  "dust": 0.02
}
```

##### Attributes Publishing
- **Topic**: `v1/devices/me/attributes`
- **Purpose**: Send device attributes and status
- **Authentication**: Device Access Token

**Payload Example**:
```json
{
  "light_status": true,
  "fan_status": false,
  "device_model": "ESP32",
  "firmware_version": "1.0.0"
}
```

##### RPC Commands (Device Control)
- **Topic**: `v1/devices/me/rpc/request/+`
- **Purpose**: Receive control commands from server
- **Response Topic**: `v1/devices/me/rpc/response/{requestId}`

**Command Example**:
```json
{
  "method": "setLightStatus",
  "params": {
    "status": true
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "message": "Light turned on successfully"
}
```

## File-specific API Usage

### function_exAI.py

**HTTP APIs Used**:
1. **OpenRouter Chat Completions API**
   - Function: `call_openrouter_chat()`
   - Purpose: NLU processing and intent extraction
   - Model: google/gemma-3-12b-it:free
   - Endpoint: `POST https://openrouter.ai/api/v1/chat/completions`

**Key Functions**:
- `parse_intent()`: Processes user input through OpenRouter API
- `ask_openrouter_with_guide()`: Handles general questions with context
- `build_system_message()`: Constructs NLU system prompts

### mqttservice_coreiot.py

**HTTP APIs Used**:
1. **ThingsBoard Telemetry API**
   - Function: `get_latest_telemetry()`
   - Purpose: Retrieve latest sensor readings
   - Endpoint: `GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries`

**MQTT APIs Used**:
1. **Telemetry Publishing**
   - Functions: `get_temperature()`, `get_humidity()`, etc.
   - Topic: `v1/devices/me/telemetry`

2. **Attributes Publishing**
   - Function: `publish_attribute()`
   - Topic: `v1/devices/me/attributes`

3. **Device Control**
   - Functions: `turn_on_light()`, `turn_off_light()`, `turn_on_fan()`, `turn_off_fan()`
   - Topics: Device-specific control topics

**WebSocket APIs Used**:
1. **Real-time Telemetry Subscription**
   - Purpose: Live sensor data streaming
   - Protocol: WebSocket over MQTT
   - Authentication: JWT Token

## AI Model Integration with OpenRouter

### OpenRouter API Configuration

The chatbot leverages **OpenRouter** as the AI service provider to access various large language models. OpenRouter acts as a unified gateway to multiple AI models, providing cost-effective and reliable access to state-of-the-art language models.

#### Key Features of OpenRouter Integration:
- **Model Access**: Direct access to Google Gemma-3-12b-it:free model
- **API Gateway**: Unified interface for multiple AI providers
- **Cost Management**: Transparent pricing and usage tracking
- **Reliability**: High availability and load balancing

### Model Selection: Google Gemma-3-12b

**Why Google Gemma-3-12b?**
- **Free Tier**: Available through OpenRouter's free tier
- **Performance**: Excellent balance of speed and accuracy for NLU tasks
- **JSON Support**: Reliable structured output generation
- **Multilingual**: Supports both English and Vietnamese contexts

### API Implementation Details

#### Authentication
```python
# OpenRouter API requires authentication via API key
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
```

#### Request Structure
```python
def call_openrouter_chat(messages, model="google/gemma-3-12b-it:free", stream=False):
    """
    Call OpenRouter API with specified model and messages
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "temperature": 0.1,  # Low temperature for consistent responses
        "max_tokens": 500    # Limit response length
    }
```

#### Intent Parsing Workflow
1. **System Message**: Defines the NLU task and JSON schema
2. **User Input**: Natural language query from user
3. **Model Processing**: Gemma-3-12b analyzes intent and entities
4. **JSON Response**: Structured output with device and action fields
5. **Validation**: Schema validation and error handling

### Response Processing

#### JSON Schema Validation
```python
schema = {
    "type": "object",
    "properties": {
        "device": {
            "type": ["string", "null"],
            "enum": valid_devices + [None]
        },
        "action": {
            "type": ["string", "null"],
            "enum": valid_actions + [None]
        }
    },
    "required": ["device", "action"]
}
```

#### Error Handling
- **JSON Parsing**: Regex extraction for malformed responses
- **Fallback Responses**: Default null values for parsing failures
- **Retry Logic**: Graceful degradation to guide-based responses

### OpenRouter Advantages

1. **Cost Efficiency**: 
   - Free tier access to premium models
   - Pay-per-use pricing for production
   - No infrastructure maintenance costs

2. **Model Diversity**:
   - Access to multiple AI providers
   - Easy model switching and comparison
   - Latest model versions automatically available

3. **Developer Experience**:
   - Simple REST API interface
   - Comprehensive documentation
   - Real-time usage monitoring

4. **Reliability**:
   - High uptime guarantees
   - Automatic failover between providers
   - Rate limiting and quota management

### Configuration Requirements

#### Environment Variables
```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

#### Model Parameters
- **Temperature**: 0.1 (low for consistent structured responses)
- **Max Tokens**: 500 (sufficient for JSON responses)
- **Stream**: False (complete responses for JSON parsing)
- **Model**: google/gemma-3-12b-it:free

## Usage Examples

### Sensor Queries
```
User: "What's the temperature?"
Bot: "Temperature now is 25.3°C."

User: "Check humidity levels"
Bot: "Humidity now is 65%."

User: "How's the air quality?"
Bot: "Temperature: 25.3°C, Humidity: 65%, Dust: 0.02 mg/cm³, Gas: 15%"
```

### Device Control
```
User: "Turn on the lights"
Bot: [Executes light control command]

User: "Is the fan running?"
Bot: [Returns fan status]
```

## Setup and Configuration

### Prerequisites
- Python 3.7+
- ThingsBoard cloud server access
- **OpenRouter API key** (free registration at openrouter.ai)
- MQTT broker configuration

### Installation
1. Clone the repository
2. Install required dependencies
3. Configure ThingsBoard connection parameters
4. **Set up OpenRouter API credentials**
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   ```
5. Deploy the chatbot service

## API Integration

### ThingsBoard Integration
- **Protocol**: MQTT over WebSocket
- **Authentication**: JWT token-based
- **Data Exchange**: JSON telemetry and attributes
- **Real-time Communication**: WebSocket API for live data

### OpenRouter AI Service Integration
- **Provider**: OpenRouter (openrouter.ai)
- **Model**: Google Gemma-3-12b-it:free
- **Endpoint**: https://openrouter.ai/api/v1/chat/completions
- **Authentication**: Bearer token authentication
- **Response Format**: Structured JSON with device and action fields
- **Fallback**: Guide-based responses for unrecognized queries
- **Rate Limiting**: Automatic handling of API quotas and limits

## Project Structure

```
BTL_IOT/
├── module/
│   ├── function_exAI.py      # AI processing and NLU with OpenRouter
│   ├── mqttservice_coreiot.py # IoT communication layer
│   └── guide.txt             # System guide for fallback responses
└── Readme.md                 # Project documentation
```

## Contributing

This project is part of a BTL (Bài Tập Lớn - Major Assignment) for IoT coursework. The chatbot demonstrates practical application of AI in IoT environments, showcasing integration between natural language processing and real-time sensor data management through modern AI APIs.

## License

This project is developed for educational purposes as part of IoT curriculum requirements.
