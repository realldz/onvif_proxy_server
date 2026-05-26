SOAP_ENV = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:soapenc="http://www.w3.org/2003/05/soap-encoding"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:tt="http://www.onvif.org/ver10/schema"
    xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
    xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
    xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"
    xmlns:timg="http://www.onvif.org/ver20/imaging/wsdl"
    xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
    xmlns:wsa="http://www.w3.org/2005/08/addressing"
    xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
    xmlns:wsbf="http://docs.oasis-open.org/wsn/bf-2">
  <soap:Body>
{body}
  </soap:Body>
</soap:Envelope>'''

PTZ_BODIES = {
    'GetServiceCapabilities': '''    <tptz:GetServiceCapabilitiesResponse>
      <tptz:Capabilities>
        <tt:EFlip>false</tt:EFlip>
        <tt:Reverse>false</tt:Reverse>
        <tt:GetCompatibleConfigurations>false</tt:GetCompatibleConfigurations>
        <tt:MoveStatus>false</tt:MoveStatus>
        <tt:StatusPosition>false</tt:StatusPosition>
      </tptz:Capabilities>
    </tptz:GetServiceCapabilitiesResponse>''',

    'GetNodes': '''    <tptz:GetNodesResponse>
      <tptz:PTZNode>
        <tt:token>default</tt:token>
        <tt:Name>DefaultPTZNode</tt:Name>
        <tt:SupportedPTZSpaces>
          <tt:AbsolutePanTiltPositionSpace>
            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</tt:URI>
            <tt:XRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:XRange>
            <tt:YRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:YRange>
          </tt:AbsolutePanTiltPositionSpace>
          <tt:RelativePanTiltTranslationSpace>
            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</tt:URI>
            <tt:XRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:XRange>
            <tt:YRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:YRange>
          </tt:RelativePanTiltTranslationSpace>
          <tt:ContinuousPanTiltVelocitySpace>
            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</tt:URI>
            <tt:XRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:XRange>
            <tt:YRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:YRange>
          </tt:ContinuousPanTiltVelocitySpace>
        </tt:SupportedPTZSpaces>
        <tt:MaximumNumberOfPresets>8</tt:MaximumNumberOfPresets>
        <tt:HomeSupported>false</tt:HomeSupported>
      </tptz:PTZNode>
    </tptz:GetNodesResponse>''',

    'GetNode': '''    <tptz:GetNodeResponse>
      <tptz:PTZNode>
        <tt:token>default</tt:token>
        <tt:Name>DefaultPTZNode</tt:Name>
        <tt:SupportedPTZSpaces>
          <tt:AbsolutePanTiltPositionSpace>
            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</tt:URI>
            <tt:XRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:XRange>
            <tt:YRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:YRange>
          </tt:AbsolutePanTiltPositionSpace>
          <tt:RelativePanTiltTranslationSpace>
            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</tt:URI>
            <tt:XRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:XRange>
            <tt:YRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:YRange>
          </tt:RelativePanTiltTranslationSpace>
          <tt:ContinuousPanTiltVelocitySpace>
            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</tt:URI>
            <tt:XRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:XRange>
            <tt:YRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:YRange>
          </tt:ContinuousPanTiltVelocitySpace>
        </tt:SupportedPTZSpaces>
        <tt:MaximumNumberOfPresets>8</tt:MaximumNumberOfPresets>
        <tt:HomeSupported>false</tt:HomeSupported>
      </tptz:PTZNode>
    </tptz:GetNodeResponse>''',

    'GetConfigurations': '''    <tptz:GetConfigurationsResponse>
      <tptz:PTZConfiguration>
        <tt:token>default</tt:token>
        <tt:Name>DefaultPTZConfiguration</tt:Name>
        <tt:NodeToken>default</tt:NodeToken>
        <tt:DefaultAbsolutePantTiltPositionSpace>
          <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</tt:URI>
        </tt:DefaultAbsolutePantTiltPositionSpace>
        <tt:DefaultRelativePanTiltTranslationSpace>
          <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</tt:URI>
        </tt:DefaultRelativePanTiltTranslationSpace>
        <tt:DefaultContinuousPanTiltVelocitySpace>
          <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</tt:URI>
        </tt:DefaultContinuousPanTiltVelocitySpace>
        <tt:PanTiltLimits>
          <tt:Range>
            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</tt:URI>
            <tt:XRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:XRange>
            <tt:YRange><tt:Min>-1.0</tt:Min><tt:Max>1.0</tt:Max></tt:YRange>
          </tt:Range>
        </tt:PanTiltLimits>
      </tptz:PTZConfiguration>
    </tptz:GetConfigurationsResponse>''',

    'GetConfiguration': '''    <tptz:GetConfigurationResponse>
      <tptz:PTZConfiguration>
        <tt:token>default</tt:token>
        <tt:Name>DefaultPTZConfiguration</tt:Name>
        <tt:NodeToken>default</tt:NodeToken>
        <tt:DefaultAbsolutePantTiltPositionSpace>
          <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</tt:URI>
        </tt:DefaultAbsolutePantTiltPositionSpace>
        <tt:DefaultRelativePanTiltTranslationSpace>
          <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</tt:URI>
        </tt:DefaultRelativePanTiltTranslationSpace>
        <tt:DefaultContinuousPanTiltVelocitySpace>
          <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</tt:URI>
        </tt:DefaultContinuousPanTiltVelocitySpace>
      </tptz:PTZConfiguration>
    </tptz:GetConfigurationResponse>''',

    'GetPresets': '''    <tptz:GetPresetsResponse/>''',

    'GetStatus': '''    <tptz:GetStatusResponse>
      <tptz:PTZStatus>
        <tt:Position>
          <tt:PanTilt x="0.0" y="0.0" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace"/>
        </tt:Position>
        <tt:MoveStatus>
          <tt:PanTilt>IDLE</tt:PanTilt>
        </tt:MoveStatus>
      </tptz:PTZStatus>
    </tptz:GetStatusResponse>''',

    'ContinuousMove': '''    <tptz:ContinuousMoveResponse/>''',
    'Stop': '''    <tptz:StopResponse/>''',
    'RelativeMove': '''    <tptz:RelativeMoveResponse/>''',
    'AbsoluteMove': '''    <tptz:AbsoluteMoveResponse/>''',
    'SetPreset': '''    <tptz:SetPresetResponse/>''',
    'GotoPreset': '''    <tptz:GotoPresetResponse/>''',
    'RemovePreset': '''    <tptz:RemovePresetResponse/>''',
    'GetCompatibleConfigurations': '''    <tptz:GetCompatibleConfigurationsResponse/>''',
}


def build_ptz_response(action_name):
    body = PTZ_BODIES.get(action_name)
    if body is None:
        body = f'    <tptz:{action_name}Response/>'
    return SOAP_ENV.format(body=body)


def build_fault(code, reason):
    body = f'''    <soap:Fault>
      <soap:Code>
        <soap:Value>soap:Sender</soap:Value>
        <soap:Subcode>
          <soap:Value>ter:{code}</soap:Value>
        </soap:Subcode>
      </soap:Code>
      <soap:Reason>
        <soap:Text xml:lang="en">{reason}</soap:Text>
      </soap:Reason>
    </soap:Fault>'''
    return SOAP_ENV.format(body=body)
