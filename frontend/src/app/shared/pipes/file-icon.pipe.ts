import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'fileIcon', standalone: true })
export class FileIconPipe implements PipeTransform {
  private readonly iconMap: Record<string, { icon: string; color: string }> = {
    'pdf': { icon: 'picture_as_pdf', color: '#F43F5E' },
    'doc': { icon: 'description', color: '#3B82F6' },
    'docx': { icon: 'description', color: '#3B82F6' },
    'xls': { icon: 'table_chart', color: '#10B981' },
    'xlsx': { icon: 'table_chart', color: '#10B981' },
    'ppt': { icon: 'slideshow', color: '#F59E0B' },
    'pptx': { icon: 'slideshow', color: '#F59E0B' },
    'txt': { icon: 'article', color: '#94A3B8' },
    'md': { icon: 'article', color: '#94A3B8' },
    'jpg': { icon: 'image', color: '#8B5CF6' },
    'jpeg': { icon: 'image', color: '#8B5CF6' },
    'png': { icon: 'image', color: '#8B5CF6' },
    'gif': { icon: 'image', color: '#8B5CF6' },
    'svg': { icon: 'image', color: '#8B5CF6' },
    'mp4': { icon: 'videocam', color: '#EC4899' },
    'mp3': { icon: 'audiotrack', color: '#06B6D4' },
    'zip': { icon: 'folder_zip', color: '#F59E0B' },
    'rar': { icon: 'folder_zip', color: '#F59E0B' },
    'csv': { icon: 'table_chart', color: '#10B981' },
    'json': { icon: 'data_object', color: '#06B6D4' },
    'html': { icon: 'code', color: '#F43F5E' },
    'css': { icon: 'code', color: '#3B82F6' },
    'js': { icon: 'code', color: '#F59E0B' },
    'ts': { icon: 'code', color: '#3B82F6' },
    'py': { icon: 'code', color: '#10B981' },
  };

  transform(fileName: string, type: 'icon' | 'color' = 'icon'): string {
    const ext = fileName.split('.').pop()?.toLowerCase() || '';
    const mapping = this.iconMap[ext] || { icon: 'insert_drive_file', color: '#64748B' };
    return type === 'icon' ? mapping.icon : mapping.color;
  }
}
