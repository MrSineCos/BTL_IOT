## Contributing

This project is part of a BTL (Bài Tập Lớn - Major Assignment) for IoT coursework. The chatbot demonstrates practical application of AI in IoT environments, showcasing integration between natural language processing and real-time sensor data management through modern AI APIs.

### Development Guidelines

#### Code Structure
- **function_exAI.py**: Focus on AI/NLU functionality and OpenRouter integration
- **mqttservice_coreiot.py**: Handle all IoT communication and ThingsBoard integration
- **guide.txt**: Maintain system documentation and fallback responses

#### Adding New Features

**Adding New Devices:**
1. Update `valid_devices` list in `function_exAI.py`
2. Add corresponding functions in `mqttservice_coreiot.py`
3. Update system message in `build_system_message()`
4. Test intent parsing with new device names

**Adding New Actions:**
1. Update `valid_actions` list in `function_exAI.py`
2. Implement action handlers in `mqttservice_coreiot.py`
3. Update JSON schema validation
4. Add usage examples to `guide.txt`

#### Testing
- Test OpenRouter API integration with various user inputs
- Verify ThingsBoard connectivity and data retrieval
- Validate JSON schema parsing and error handling
- Test fallback responses for unrecognized intents

### Best Practices
- Keep API keys secure and use environment variables
- Implement proper error handling for network requests
- Use structured logging for debugging
- Follow JSON schema validation patterns
- Maintain backward compatibility when updating APIs

## Troubleshooting

### Common Issues

#### OpenRouter API Issues
```python
# Check API key configuration
import os
api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print("OpenRouter API key not found")
```

#### ThingsBoard Connection Issues
```python
# Verify ThingsBoard credentials
# Check MQTT broker connectivity
# Validate device tokens and permissions
```

#### Intent Parsing Issues
- Verify JSON schema validation
- Check model response format
- Test with different user input variations
- Review system message construction

### Debug Mode
Enable debug logging to troubleshoot issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization

### OpenRouter API Optimization
- Use appropriate temperature settings (0.1 for consistent responses)
- Limit max_tokens to reduce latency and costs
- Implement request caching for repeated queries
- Handle rate limiting gracefully

### ThingsBoard Optimization
- Use WebSocket connections for real-time data
- Implement connection pooling for HTTP requests
- Cache telemetry data to reduce API calls
- Optimize MQTT message frequency

## Security Considerations

### API Security
- Store API keys in environment variables
- Use HTTPS for all API communications
- Implement request validation and sanitization
- Monitor API usage and set quotas

### IoT Security
- Secure MQTT connections with TLS
- Validate device authentication tokens
- Implement proper access controls
- Monitor for unusual device behavior

## Deployment

### Local Development
```bash
# Set environment variables
export OPENROUTER_API_KEY="your_key_here"
export THINGSBOARD_HOST="your_thingsboard_host"
export THINGSBOARD_TOKEN="your_jwt_token"

# Run the application
python main.py
```

### Production Deployment
- Use container orchestration (Docker/Kubernetes)
- Implement health checks and monitoring
- Set up logging and alerting
- Configure auto-scaling based on usage

### Environment Configuration
```bash
# Production environment variables
OPENROUTER_API_KEY=prod_api_key
THINGSBOARD_HOST=production.thingsboard.cloud
THINGSBOARD_TOKEN=production_jwt_token
LOG_LEVEL=INFO
CACHE_ENABLED=true
```

## Monitoring and Analytics

### API Monitoring
- Track OpenRouter API usage and costs
- Monitor response times and error rates
- Set up alerts for API quota limits
- Analyze intent parsing accuracy

### IoT Monitoring
- Monitor device connectivity status
- Track telemetry data quality
- Alert on sensor anomalies
- Monitor MQTT message throughput

### User Analytics
- Track user query patterns
- Analyze successful vs failed intents
- Monitor response satisfaction
- Identify common user needs

## Future Enhancements

### Planned Features
1. **Multi-language Support**: Extend Vietnamese language capabilities
2. **Voice Integration**: Add speech-to-text and text-to-speech
3. **Advanced Analytics**: Implement predictive analytics for sensor data
4. **Mobile App**: Develop companion mobile application
5. **Dashboard Integration**: Web-based control dashboard

### Technical Improvements
1. **Caching Layer**: Implement Redis for response caching
2. **Load Balancing**: Distribute API requests across multiple instances
3. **Database Integration**: Store conversation history and analytics
4. **Webhook Support**: Real-time notifications for critical events
5. **API Rate Limiting**: Implement intelligent request throttling

### AI Model Enhancements
1. **Custom Fine-tuning**: Train domain-specific models
2. **Context Awareness**: Maintain conversation context
3. **Learning Capabilities**: Improve responses based on user feedback
4. **Multi-modal Input**: Sensor data analysis, weather analysis

## License

This project is developed for educational purposes as part of IoT curriculum requirements. 

### Educational Use License
- **Purpose**: Academic learning and research
- **Scope**: IoT system integration and AI application development
- **Restrictions**: Commercial use requires separate licensing
- **Attribution**: Credit original authors and educational institution

### Third-party Licenses
- **OpenRouter**: Subject to OpenRouter Terms of Service
- **ThingsBoard**: Apache License 2.0
- **Python Libraries**: Various open-source licenses (see requirements.txt)

## Acknowledgments

### Educational Institution
- Course: IoT Systems and Applications
- University: Ho Chi Minh University of Technology
- Academic Year: [2025]
- Academic Department: [Department of Computer Science/Engineering]

### Technology Partners
- **OpenRouter**: AI model access and API services
- **ThingsBoard**: IoT platform and cloud services
- **Google**: Gemma model development
- **Python Community**: Open-source libraries and frameworks

### Contributors
- [Nguyễn Công Vũ]: AI integration and NLU development, System architecture and documentation, IoT communication between Chatbot and CoreIoT(based on Thingsboard platform)

## Contact and Support
- **Email**: [vu.nguyencong@hcmut.edu.vn]

### Technical Support
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Refer to inline code comments and API documentation
- **Community**: Join IoT development forums and communities

### Project Repository
- **GitHub**: https://github.com/MrSineCos/BTL_IOT
- **Documentation**: See README.md and inline comments
- **Examples**: Check examples/ directory for usage samples

---

**Note**: This project demonstrates the integration of modern AI services with IoT platforms for educational purposes. The implementation showcases practical applications of natural language processing in IoT device management and real-time sensor data analysis.
