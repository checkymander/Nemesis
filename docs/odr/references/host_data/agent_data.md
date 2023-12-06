# Agent Data
Date type: `agent_data`

## Overview
Information about the currently running agent.

| Parameters           | Format          | Description                                                |
| -------------------- | --------------- | ---------------------------------------------------------- |
| id                   | string          | The ID of the agent                                        |
| username             | string          | The username the agent is running in the context of        |
| hostname             | string          | The host the agent is running on                           |
| domain               | string          | The domain context of the agent                            |
| process_id           | int             | Process ID                                                 |
| process_name         | string          | The name of the process the agent is running in            |
| arch                 | string          | Architecture of the agent process (e.g., x86, x64, arm)    |
| os                   | string          | OS Version                                                 |
| integrity_level      | int             | Agent Integrity Level                                      |
| ips                  | string[]        | List of IP Addresses returned by the agent                 |
| callback_time        | datetime        | Time the process was started, if known                     |

### Integrity Level

Integrity levels are defined as follows:

```
enum IntegrityLevel {
    LOW = 1,
    MEDIUM = 2,
    HIGH = 3,
    SYSTEM = 4
}
```

## Protobuf Definition

**ProcessIngestionMessage** and **ProcessIngestion** in *nemesis.proto*

## Examples
```json
{
    "data":[
        ...
        {
            "id": "775643a6-9e40-4ffe-bb88-0420c8752f91",
            "username": "john",
            "hostname": "john-pc",
            "domain": "WORKGROUP",
            "process_id": 1234,
            "process_name" : "notepad.exe",
            "arch" : "x64",
            "os" : "Microsoft Windows 11 Pro",
            "integrity_level" : 2,
            "ips" : [
                "127.0.0.1",
                "192.168.1.1",
                "10.4.25.20"
            ],
            "callback_time": "2012-04-23T18:25:43.511Z"
        },
    "metadata": {
        "agent_id": "339429212",
        "agent_type": "beacon",
        "automated": 1,
        "data_type": "registry_value",
        "expiration": "2023-08-01T22:51:35",
        "source": "DC",
        "project": "ASSESS-X",
        "timestamp": "2022-08-01T22:51:35"
    }
    ]
}
```

