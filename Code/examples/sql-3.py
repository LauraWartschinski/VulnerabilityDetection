#db_processor_mysql.py
import asyncio
import tormysql

_pool = None
_handler = None

def set_log_handler(handler):
    '''db관련 에러메시지를 처리할 핸들러를 등록한다.'''
    global _handler
    _handler = handler

def connect_db_server(host_addr, user_id, password, db, loop):
    '''db pool을 연다.'''
    global _pool
    _pool = tormysql.ConnectionPool(
        max_connections = 20,
        idle_seconds = 7200,
        wait_connection_timeout = 3,
        host = host_addr,
        user = user_id,
        passwd = password,
        db = db,
        charset = "utf8")

    return loop.run_until_complete(is_connect_db())

async def is_connect_db():
    try:
        async with await _pool.Connection():
            pass
    except Exception as ex:
        _error_report(ex)
        return False

    return True

async def create_account(name: str, password: str):
    '''db에 계정을 생성한다.'''
    global _pool
    uid = -1
    async with await _pool.Connection() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(\
                    "INSERT INTO player (name, password, lv, xp, hp) values ('%s', '%s', 1, 0, 150)"\
                    % (name, password))
                uid = conn.insert_id()
        except Exception as ex:
            await conn.rollback()
            _error_report(ex)
            return False, -1  
        await conn.commit()

    return True, uid

async def get_player_info(name: str) -> tuple:
    '''db에서 플레이어 정보를 얻어온다.'''
    global _pool
    async with await _pool.Connection() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT uid, name, password, lv, xp, hp FROM player where name = '%s'" % name)
                data = cursor.fetchone()
        except Exception as ex:
            _error_report(ex)
            return tuple()

    if data is None:
        return tuple()

    return data

async def update_level_and_xp(name: str, lv: int, xp: int):
    '''level, xp 정보를 업데이트 한다.'''
    global _pool
    async with await _pool.Connection() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("UPDATE player SET lv=%d, xp=%d where name = '%s'" % (lv, xp, name))
        except Exception as ex:
            _error_report(ex)
            return False
        await conn.commit() 

    return True

async def update_hp(name: str, hp: int):
    '''hp 정보를 업데이트 한다.'''
    global _pool
    async with await _pool.Connection() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("UPDATE player SET hp=%d where name = '%s'" % (hp, name))
        except Exception as ex:
            _error_report(ex)
            return False
        await conn.commit() 

    return True

async def create_item(player_uid:int, item_id: int):
    '''db에 아이템을 추가한다.'''
    global _pool
    uid = -1
    async with await _pool.Connection() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("INSERT INTO item (player_uid, item_id)\
                 values (%d, %d)" % (player_uid, item_id))
            uid = conn.insert_id()
        except Exception as ex:
            _error_report(ex)
            return False, -1
        await conn.commit()

    return True, uid

async def get_item_list(player_uid: int):
    '''db에서 특정 플레이어의 소유 아이템 리스트를 얻어온다.'''
    global _pool
    async with await _pool.Connection() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT uid, item_id FROM item where player_uid = %d" % player_uid)
                datas = cursor.fetchall()
        except Exception as ex:
            _error_report(ex)
            return tuple(), False

    return datas, True

def close():
    '''db pool을 종료한다.'''
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None

def _error_report(err_msg):
    '''에러 핸들러로 에러메시지를 던진다.'''
    global _handler
    if _handler:
        _handler(err_msg)

if __name__ == '__main__':
    def error_handler(msg):
        print(msg)

    loop = asyncio.get_event_loop()
    set_log_handler(error_handler)
    result = connect_db_server('127.0.0.1', 'root', 'Mysql12345', 'mud_db', loop)
    print('db connect result is ' + str(result))
    loop.run_until_complete(create_item(37, 0))
    close()


