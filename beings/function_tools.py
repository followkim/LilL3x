function_tools =  [
#    {
#    "type":"function",
#    "function": {
#        "name": "SetEvent",
#        "description": "Return the date and time for an upcoming event.  Call when a user describes a future event, for example when the user says 'Have have a doctors appoint tomarrow'",
#        "parameters": {
#            "type": "object",
#            "properties": {
#                "event_name": {
#                    "type": "string",
#                    "description": "The description of the event.",
#                },
#                "event_date": {
#                    "type": "string",
#                    "description": "The date and (if applicable) the time",
#                },
#            },
#            "required": ["event_name", "event_date"],
#            "additionalProperties": False,
#        }
#     }
#  },
  {
    "type":"function",
    "function": {
        "name": "TakePictureToolCall",
        "description": "Take a picture with the attached camera.  Call when the user indicates they want you to look at something or see where they are.",
        "parameters": {
            "type": "object",
            "properties": {
                "picture_context": {
                    "type": "string",
                    "description": "The description and context of the picture subject.",
                },
            },
            "required": ["picture_subject"],
            "additionalProperties": False,
        }
     }
  }
]
