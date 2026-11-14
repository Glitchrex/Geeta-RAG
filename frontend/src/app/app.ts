import { Component, signal } from '@angular/core';
import { Upload } from './components/upload/upload';
import { Chat } from './components/chat/chat';
import { DocumentInfo } from './app.service';

@Component({
  imports: [Upload, Chat],
  selector: 'app-root',
  template: `
  <main>
  <h1> Geeta - RAG </h1>
  <p class="hint">Upload a Document in PDF format, then ask questions based on it. Every answer cites the pages it used. </p>
  <app-upload (started)="activeDoc.set(null)" (ready)="activeDoc.set($event)" />
  
  @if(activeDoc(); as doc) {
      <app-chat [documentId] = "doc.id" />
  }
  </main>
  `
})
export class App {
  protected readonly title = signal('frontend');
  activeDoc = signal<DocumentInfo | null>(null);
}
