import { HttpClient, HttpEvent } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable } from "rxjs";

const API_URL = "http://localhost:8000";

export interface DocumentInfo {
    id: string;
    filename: string;
    status : 'processing' | 'done' | 'pending' | 'failed';
    error: string | null;
    total_chunks : number;
    embedded_chunks: number;
    created_at: string;
}

export interface Source {
    n : number;
    page: number;
    preview : string;
}

export interface ChatHandlers {
    onSources: (sources: Source[]) => void;
    onToken: (token: string) => void;
    onError: (message: string) => void;
}

@Injectable({ providedIn: 'root' })
export class APIService {
    private http = inject(HttpClient);

    upload(file: File): Observable<HttpEvent<DocumentInfo>> {
        const form = new FormData();
        form.append('file',file);
        return this.http.post<DocumentInfo>(`${API_URL}/documents`, form,{
            reportProgress: true,
            observe: 'events',
        });
    }

    getDocument(id:string):Observable<DocumentInfo>{
        return this.http.get<DocumentInfo>(`${API_URL}/documents/${id}`)
    }

    async streamChat(documentId: string, question: string, handlers: ChatHandlers): Promise<void>{
        let response: Response;
        try {
            response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type' : 'application/json'},
                body: JSON.stringify({document_id: documentId, question })
            });
        }
        catch {
            handlers.onError("Can't reach the API. Start the backend on port 8000.");
            return;
        }

        if(!response.ok || !response.body) {
            const body = await response.json().catch(() => null);
            handlers.onError(body?.detail ?? `Request failed with status ${response.status}`);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while(true){
            const {value , done} = await reader.read();
            if(done) break;
            buffer += decoder.decode(value, {stream:true});
            const events = buffer.split('\n\n');
            buffer = events.pop() ?? '';
            events.forEach((raw) => this.dispatch(raw,handlers));
        }
    }

    private dispatch(raw: string, handlers: ChatHandlers): void {
        let event = 'message';
        let data = '';
        for (const line of raw.split('\n')) {
            const cleanLine = line.endsWith('\r') ? line.slice(0, -1) : line;
            if (cleanLine.startsWith('event: ')) event = cleanLine.slice(7).trim();
            if (cleanLine.startsWith('data: ')) data += cleanLine.slice(6);
        }
        if (!data) return;

        try {
            const payload = JSON.parse(data);
            if (event === 'sources') handlers.onSources(payload);
            if (event === 'message') handlers.onToken(payload);
            if (event === 'error') handlers.onError(payload);
        } catch (e) {
            console.error('Failed to parse SSE payload:', data, e);
        }
    }

}