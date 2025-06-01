import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import os

class NewsDatabase:
    """新闻数据库服务"""
    
    def __init__(self, db_path: str = "data/news.db"):
        """初始化数据库
        
        Args:
            db_path: str 数据库文件路径
        """
        self.db_path = db_path
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        # 检查并执行数据库迁移
        self._migrate_database()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查表是否已存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_items'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # 创建新表（包含subtitle字段的结构）
                cursor.execute('''
                    CREATE TABLE news_items (
                        id TEXT PRIMARY KEY,
                        manager_name TEXT,
                        source_type TEXT NOT NULL,
                        source_name TEXT NOT NULL,
                        published DATETIME NOT NULL,
                        title TEXT NOT NULL,
                        subtitle TEXT,
                        summary TEXT,
                        content TEXT NOT NULL,
                        link TEXT NOT NULL,
                        fetch_timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                        raw_data TEXT
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX idx_published ON news_items(published)')
                cursor.execute('CREATE INDEX idx_source_name ON news_items(source_name)')
                cursor.execute('CREATE INDEX idx_source_type ON news_items(source_type)')
                cursor.execute('CREATE INDEX idx_fetch_timestamp ON news_items(fetch_timestamp)')
                cursor.execute('CREATE INDEX idx_fetch_date ON news_items(date(fetch_timestamp))')
                
                print("创建了包含subtitle字段的数据库结构")
            
            conn.commit()
    
    def _migrate_database(self):
        """数据库迁移：处理从旧结构到新结构的升级"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查当前表结构
            cursor.execute("PRAGMA table_info(news_items)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            # 检查并执行数据库迁移
            self._migrate_database_if_needed(cursor, conn)
            
            conn.commit()
    
    def _migrate_database_if_needed(self, cursor, conn):
        """检查并执行必要的数据库迁移"""
        # 获取当前表结构
        cursor.execute("PRAGMA table_info(news_items)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 检查是否需要添加subtitle字段
        if 'subtitle' not in columns:
            print("检测到缺少subtitle字段，开始添加...")
            self._migrate_add_subtitle(cursor, conn)
            return
        
        # 检查是否需要从旧结构迁移
        if 'source' in columns and 'source_name' not in columns:
            print("检测到旧表结构，开始迁移...")
            self._migrate_from_old_structure(cursor, conn)
            return
        
        # 检查是否有created_at字段需要重命名
        if 'created_at' in columns and 'fetch_timestamp' not in columns:
            print("检测到created_at字段，开始重命名迁移...")
            self._migrate_created_at_to_fetch_timestamp(cursor, conn)
            return
        
        # 检查是否有fetch_date字段需要删除
        if 'fetch_date' in columns:
            print("检测到冗余的fetch_date字段，开始去除...")
            self._migrate_remove_fetch_date(cursor, conn)
            return
        
        # 检查字段顺序是否需要调整（通过检查第2个字段是否为manager_name）
        if len(columns) > 1 and columns[1] != 'manager_name':
            print("检测到字段顺序需要调整，开始重排...")
            self._migrate_reorder_fields(cursor, conn)
            return
    
    def _migrate_from_old_structure(self, cursor, conn):
        """从旧结构迁移到新结构"""
        try:
            # 创建新表
            cursor.execute('''
                CREATE TABLE news_items_new (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    manager_name TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    published DATETIME NOT NULL,
                    link TEXT NOT NULL,
                    fetch_date DATE NOT NULL,
                    fetch_timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                    raw_data TEXT
                )
            ''')
            
            # 迁移数据
            cursor.execute('''
                INSERT INTO news_items_new 
                (id, source_name, source_type, manager_name, title, content, summary, 
                 published, link, fetch_date, fetch_timestamp, raw_data)
                SELECT 
                    id, 
                    COALESCE(source, '未知来源') as source_name,
                    source_type,
                    COALESCE(source, 'RSS聚合') as manager_name,
                    title, 
                    content, 
                    summary, 
                    published, 
                    link, 
                    fetch_date, 
                    COALESCE(created_at, CURRENT_TIMESTAMP) as fetch_timestamp,
                    raw_data
                FROM news_items
            ''')
            
            # 删除旧表并重命名
            cursor.execute('DROP TABLE news_items')
            cursor.execute('ALTER TABLE news_items_new RENAME TO news_items')
            
            # 创建索引
            self._create_indexes(cursor)
            
            conn.commit()
            print("从旧结构迁移完成！")
            
        except Exception as e:
            print(f"从旧结构迁移失败: {str(e)}")
            conn.rollback()
            raise
    
    def _migrate_created_at_to_fetch_timestamp(self, cursor, conn):
        """将created_at字段重命名为fetch_timestamp"""
        try:
            # 创建新表
            cursor.execute('''
                CREATE TABLE news_items_new (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    manager_name TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    published DATETIME NOT NULL,
                    link TEXT NOT NULL,
                    fetch_date DATE NOT NULL,
                    fetch_timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                    raw_data TEXT
                )
            ''')
            
            # 迁移数据（created_at重命名为fetch_timestamp）
            cursor.execute('''
                INSERT INTO news_items_new 
                (id, source_name, source_type, manager_name, title, content, summary, 
                 published, link, fetch_date, fetch_timestamp, raw_data)
                SELECT 
                    id, source_name, source_type, manager_name, title, content, summary, 
                    published, link, fetch_date, created_at as fetch_timestamp, raw_data
                FROM news_items
            ''')
            
            # 删除旧表并重命名
            cursor.execute('DROP TABLE news_items')
            cursor.execute('ALTER TABLE news_items_new RENAME TO news_items')
            
            # 创建索引
            self._create_indexes(cursor)
            
            conn.commit()
            print("字段重命名迁移完成！")
            
        except Exception as e:
            print(f"字段重命名迁移失败: {str(e)}")
            conn.rollback()
            raise
    
    def _migrate_remove_fetch_date(self, cursor, conn):
        """去掉冗余的fetch_date字段"""
        try:
            # 创建新表
            cursor.execute('''
                CREATE TABLE news_items_new (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    manager_name TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    published DATETIME NOT NULL,
                    link TEXT NOT NULL,
                    fetch_timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                    raw_data TEXT
                )
            ''')
            
            # 迁移数据（去掉fetch_date）
            cursor.execute('''
                INSERT INTO news_items_new 
                (id, source_name, source_type, manager_name, title, content, summary, 
                 published, link, fetch_timestamp, raw_data)
                SELECT 
                    id, source_name, source_type, manager_name, title, content, summary, 
                    published, link, fetch_timestamp, raw_data
                FROM news_items
            ''')
            
            # 删除旧表并重命名
            cursor.execute('DROP TABLE news_items')
            cursor.execute('ALTER TABLE news_items_new RENAME TO news_items')
            
            # 创建索引
            self._create_indexes(cursor)
            
            conn.commit()
            print("冗余字段迁移完成！")
            
        except Exception as e:
            print(f"冗余字段迁移失败: {str(e)}")
            conn.rollback()
            raise
    
    def _migrate_fix_timezone(self, cursor, conn):
        """修复UTC时间戳问题"""
        try:
            # 创建新表
            cursor.execute('''
                CREATE TABLE news_items_new (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    manager_name TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    published DATETIME NOT NULL,
                    link TEXT NOT NULL,
                    fetch_timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                    raw_data TEXT
                )
            ''')
            
            # 迁移数据（修复时间戳）
            cursor.execute('''
                INSERT INTO news_items_new 
                (id, source_name, source_type, manager_name, title, content, summary, 
                 published, link, fetch_timestamp, raw_data)
                SELECT 
                    id, source_name, source_type, manager_name, title, content, summary, 
                    published, link, datetime(fetch_timestamp, "localtime"), raw_data
                FROM news_items
            ''')
            
            # 删除旧表并重命名
            cursor.execute('DROP TABLE news_items')
            cursor.execute('ALTER TABLE news_items_new RENAME TO news_items')
            
            # 创建索引
            self._create_indexes(cursor)
            
            conn.commit()
            print("UTC时间戳修复完成！")
            
        except Exception as e:
            print(f"UTC时间戳修复失败: {str(e)}")
            conn.rollback()
            raise
    
    def _migrate_reorder_fields(self, cursor, conn):
        """重新排列字段顺序，按照业务重要性"""
        try:
            # 创建新表（按重要性排序字段）
            cursor.execute('''
                CREATE TABLE news_items_new (
                    id TEXT PRIMARY KEY,
                    manager_name TEXT,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    published DATETIME NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT NOT NULL,
                    link TEXT NOT NULL,
                    fetch_timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                    raw_data TEXT
                )
            ''')
            
            # 迁移数据（新的字段顺序）
            cursor.execute('''
                INSERT INTO news_items_new 
                (id, manager_name, source_type, source_name, published, title, summary, 
                 content, link, fetch_timestamp, raw_data)
                SELECT 
                    id, manager_name, source_type, source_name, published, title, summary, 
                    content, link, fetch_timestamp, raw_data
                FROM news_items
            ''')
            
            # 删除旧表并重命名
            cursor.execute('DROP TABLE news_items')
            cursor.execute('ALTER TABLE news_items_new RENAME TO news_items')
            
            # 创建索引
            self._create_indexes(cursor)
            
            conn.commit()
            print("字段顺序重排完成！")
            
        except Exception as e:
            print(f"字段顺序重排失败: {str(e)}")
            conn.rollback()
            raise
    
    def _migrate_add_subtitle(self, cursor, conn):
        """添加subtitle字段的迁移"""
        try:
            # 创建新表（包含subtitle字段）
            cursor.execute('''
                CREATE TABLE news_items_new (
                    id TEXT PRIMARY KEY,
                    manager_name TEXT,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    published DATETIME NOT NULL,
                    title TEXT NOT NULL,
                    subtitle TEXT,
                    summary TEXT,
                    content TEXT NOT NULL,
                    link TEXT NOT NULL,
                    fetch_timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                    raw_data TEXT
                )
            ''')
            
            # 迁移数据（添加空的subtitle字段）
            cursor.execute('''
                INSERT INTO news_items_new 
                (id, manager_name, source_type, source_name, published, title, subtitle, summary, 
                 content, link, fetch_timestamp, raw_data)
                SELECT 
                    id, manager_name, source_type, source_name, published, title, '', summary, 
                    content, link, fetch_timestamp, raw_data
                FROM news_items
            ''')
            
            # 删除旧表并重命名
            cursor.execute('DROP TABLE news_items')
            cursor.execute('ALTER TABLE news_items_new RENAME TO news_items')
            
            # 创建索引
            self._create_indexes(cursor)
            
            conn.commit()
            print("subtitle字段添加完成！")
            
        except Exception as e:
            print(f"添加subtitle字段失败: {str(e)}")
            conn.rollback()
            raise
    
    def _create_indexes(self, cursor):
        """创建数据库索引"""
        cursor.execute('CREATE INDEX idx_published ON news_items(published)')
        cursor.execute('CREATE INDEX idx_source_name ON news_items(source_name)')
        cursor.execute('CREATE INDEX idx_source_type ON news_items(source_type)')
        cursor.execute('CREATE INDEX idx_fetch_timestamp ON news_items(fetch_timestamp)')
        cursor.execute('CREATE INDEX idx_fetch_date ON news_items(date(fetch_timestamp))')
    
    def save_news_batch(self, news_list: List[Dict]) -> int:
        """批量保存新闻数据
        
        Args:
            news_list: List[Dict] 新闻列表
        
        Returns:
            int 成功保存的新闻数量
        """
        if not news_list:
            return 0
        
        saved_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for news in news_list:
                try:
                    # 检查是否已存在
                    cursor.execute('SELECT id FROM news_items WHERE id = ?', (news['id'],))
                    if cursor.fetchone():
                        print(f"新闻已存在，跳过: {news['title']}")
                        continue
                    
                    # 处理发布时间 - 只存储日期部分
                    published = news['published']
                    if isinstance(published, str):
                        published = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    
                    # 只保留日期部分，去掉时间和时区信息
                    published_date_only = published.date()
                    
                    # 获取当前本地时间作为抓取时间戳
                    fetch_timestamp = datetime.now()
                    
                    # 插入新闻（包含subtitle字段的结构）
                    cursor.execute('''
                        INSERT INTO news_items 
                        (id, manager_name, source_type, source_name, published, title, subtitle, summary, content, link, fetch_timestamp, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        news['id'],
                        news.get('manager_name', news.get('source', 'RSS聚合')),  # 管理器名称
                        news['source_type'],
                        news.get('source_name', news.get('source', '未知来源')),  # 优先使用source_name
                        published_date_only,  # 只存储日期
                        news['title'],
                        news.get('subtitle', ''),  # 副标题字段
                        news.get('summary', ''),
                        news['content'],
                        news['link'],
                        fetch_timestamp,
                        json.dumps(news.get('raw_data', {}), ensure_ascii=False)
                    ))
                    
                    saved_count += 1
                    print(f"保存新闻: {news['title']}")
                    
                except Exception as e:
                    print(f"保存新闻失败: {news.get('title', 'Unknown')} - {str(e)}")
                    continue
            
            conn.commit()
        
        print(f"\n批量保存完成: 成功保存 {saved_count}/{len(news_list)} 条新闻")
        return saved_count
    
    def get_news_by_date(self, target_date: date) -> List[Dict]:
        """根据抓取日期检索新闻
        
        Args:
            target_date: date 目标日期
        
        Returns:
            List[Dict] 新闻列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM news_items 
                WHERE date(fetch_timestamp) = ? 
                ORDER BY published DESC
            ''', (target_date,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_news_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """根据日期范围检索新闻
        
        Args:
            start_date: date 开始日期
            end_date: date 结束日期
        
        Returns:
            List[Dict] 新闻列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM news_items 
                WHERE date(fetch_timestamp) BETWEEN ? AND ? 
                ORDER BY published DESC
            ''', (start_date, end_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_news_by_source(self, source_name: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict]:
        """根据新闻来源检索新闻
        
        Args:
            source_name: str 新闻来源名称
            start_date: Optional[date] 开始日期
            end_date: Optional[date] 结束日期
        
        Returns:
            List[Dict] 新闻列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if start_date and end_date:
                cursor.execute('''
                    SELECT * FROM news_items 
                    WHERE source_name = ? AND date(fetch_timestamp) BETWEEN ? AND ?
                    ORDER BY published DESC
                ''', (source_name, start_date, end_date))
            else:
                cursor.execute('''
                    SELECT * FROM news_items 
                    WHERE source_name = ?
                    ORDER BY published DESC
                ''', (source_name,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_news(self, keyword: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict]:
        """根据关键词搜索新闻
        
        Args:
            keyword: str 搜索关键词
            start_date: Optional[date] 开始日期
            end_date: Optional[date] 结束日期
        
        Returns:
            List[Dict] 新闻列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            keyword_pattern = f'%{keyword}%'
            
            if start_date and end_date:
                cursor.execute('''
                    SELECT * FROM news_items 
                    WHERE (title LIKE ? OR content LIKE ?) 
                    AND date(fetch_timestamp) BETWEEN ? AND ?
                    ORDER BY published DESC
                ''', (keyword_pattern, keyword_pattern, start_date, end_date))
            else:
                cursor.execute('''
                    SELECT * FROM news_items 
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY published DESC
                ''', (keyword_pattern, keyword_pattern))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息
        
        Returns:
            Dict 统计信息
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 总新闻数
            cursor.execute('SELECT COUNT(*) FROM news_items')
            total_news = cursor.fetchone()[0]
            
            # 按来源统计
            cursor.execute('''
                SELECT source_name, COUNT(*) as count 
                FROM news_items 
                GROUP BY source_name 
                ORDER BY count DESC
            ''')
            source_stats = dict(cursor.fetchall())
            
            # 按日期统计
            cursor.execute('''
                SELECT date(fetch_timestamp) as fetch_date, COUNT(*) as count 
                FROM news_items 
                GROUP BY date(fetch_timestamp) 
                ORDER BY date(fetch_timestamp) DESC 
                LIMIT 10
            ''')
            date_stats = dict(cursor.fetchall())
            
            # 最新和最早的新闻
            cursor.execute('SELECT MIN(date(fetch_timestamp)), MAX(date(fetch_timestamp)) FROM news_items')
            date_range = cursor.fetchone()
            
            return {
                'total_news': total_news,
                'source_stats': source_stats,
                'recent_date_stats': date_stats,
                'date_range': {
                    'earliest': date_range[0],
                    'latest': date_range[1]
                }
            }
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """清理旧数据
        
        Args:
            days_to_keep: int 保留天数，默认90天
        
        Returns:
            int 删除的记录数
        """
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM news_items WHERE date(fetch_timestamp) < ?', (cutoff_date,))
            count_to_delete = cursor.fetchone()[0]
            
            cursor.execute('DELETE FROM news_items WHERE date(fetch_timestamp) < ?', (cutoff_date,))
            conn.commit()
            
            print(f"清理了 {count_to_delete} 条超过 {days_to_keep} 天的旧新闻")
            return count_to_delete
    
    def clear_all_data(self) -> int:
        """清空所有新闻数据
        
        Returns:
            int 删除的记录数
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM news_items')
            total_count = cursor.fetchone()[0]
            
            cursor.execute('DELETE FROM news_items')
            conn.commit()
            
            print(f"已清空所有数据，共删除 {total_count} 条新闻")
            return total_count 