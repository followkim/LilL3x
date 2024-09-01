from datetime import datetime

class Messages:
    messages = []
    
    def __init__(self):
        return
 
    def GetMessage(self):
        if self.messages:
            return self.messages.pop()
        return False

    def GetMessages(self):
        ms = self.messages
        self.messages = []
        return ms

    def SetMessage(self, type, message, dt=datetime.now()):
        self.messages.append([type, message, dt])
        print(f"Message added to Q: {self.messages[-1][0]} : {self.messages[-1][1]}")
        return self.messages

if __name__ == '__main__':


   ms = Messages()
   ms.SetMessage('mood', 'sad', datetime.now())
   ms.SetMessage('Evesdrop', 'i like pie', datetime.now())
   ms.SetMessage('mood', 'angry', datetime.now())

   for m in ms.GetMessages():
       print(f'MessageType: {m[0]}')
       print(f'MessageContent: {m[1]}')
       print(f'MessageDT: {m[2]}')
   print(f'Try Pop Empty message Q: {ms.GetMessage()}') # should return false

