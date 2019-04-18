from functools import wraps

def bounds(min_, max_, n):
    '''Helper function to return min, or max or inbetween if in bounds'''
    return min(max_, max(min_, n))

def flagger(flag):
    def wrap(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            self.bot.flags[flag].add(self.ctx.message.channel.id)
            print(f'Flagging {self} with {flag}')
            try:
                result = await func(self, *args, **kwargs)
            finally:
                self.bot.flags[flag].remove(self.ctx.message.channel.id)
                print(f'Unflagged {flag} from {self}')

            return result

        return wrapper
    return wrap